# apps/worker/olympus_worker/main.py
from __future__ import annotations

import asyncio
import json
import os
import random
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import requests

from packages.memory.olympus_memory.db import MemoryDB
from packages.plan.olympus_plan.models import Guard, Plan, PlanEvent, PlanState, Step, StepState
from packages.tools.olympus_tools import fs as fstool
from packages.tools.olympus_tools import (
    glob_paths as tool_glob,
    search_file_content as tool_search,
    run_shell_command as tool_shell,
    git_status as tool_git_status,
    git_add as tool_git_add,
    git_commit as tool_git_commit,
)

CONCURRENCY = int(os.getenv("OLY_EXEC_CONCURRENCY", "2"))
AUTO_CONSENT = os.getenv("OLY_AUTO_CONSENT", "true").lower() == "true"  # dev convenience

def now_ms() -> int:
    return int(time.time() * 1000)

def log(msg: str, **fields):
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()), "msg": msg, **fields}
    print(json.dumps(rec, ensure_ascii=False))

# ------------------ Tool Registry ------------------

class ToolError(Exception): ...

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Any] = {}
        # register built-ins
        self.register("fs.read", self._fs_read, scopes=[fstool.READ_SCOPE])
        self.register("fs.write", self._fs_write, scopes=[fstool.WRITE_SCOPE])
        self.register("fs.delete", self._fs_delete, scopes=[fstool.DELETE_SCOPE])
        self.register("fs.list", self._fs_list, scopes=[fstool.LIST_SCOPE])
        self.register("net.http_get", self._http_get, scopes=["net_get"])
        # Developer tools
        self.register("fs.glob", self._fs_glob, scopes=[fstool.LIST_SCOPE])
        self.register("fs.search", self._fs_search, scopes=["search_fs"])  # custom scope
        self.register("shell.run", self._shell_run, scopes=["exec_shell"])  # custom scope
        self.register("git.status", self._git_status, scopes=["git_ops"])  # custom scope
        self.register("git.add", self._git_add, scopes=["git_ops"])  # custom scope
        self.register("git.commit", self._git_commit, scopes=["git_ops"])  # custom scope

    def register(self, name: str, fn, scopes: List[str]):
        self._tools[name] = {"fn": fn, "scopes": scopes}

    def resolve(self, name: str):
        if name not in self._tools:
            raise ToolError(f"Unknown tool: {name}")
        return self._tools[name]

    # ---- implementations ----
    def _fs_read(self, args: Dict[str, Any], consent: Optional[fstool.ConsentToken]) -> Dict[str, Any]:
        return fstool.read_file(args["path"], token=consent)

    def _fs_write(self, args: Dict[str, Any], consent: Optional[fstool.ConsentToken]) -> Dict[str, Any]:
        return fstool.write_file(args["path"], args["content"], overwrite=args.get("overwrite", True), token=consent)

    def _fs_delete(self, args: Dict[str, Any], consent: Optional[fstool.ConsentToken]) -> Dict[str, Any]:
        return fstool.delete_path(args["path"], recursive=args.get("recursive", False), token=consent)

    def _fs_list(self, args: Dict[str, Any], consent: Optional[fstool.ConsentToken]) -> Dict[str, Any]:
        return fstool.list_dir(args.get("path", "/"), token=consent)

    def _http_get(self, args: Dict[str, Any], consent: Optional[fstool.ConsentToken]) -> Dict[str, Any]:
        # Enforce consent for network access when required
        if fstool.REQUIRE_CONSENT:
            if consent is None or ("*" not in consent.scopes and "net_get" not in consent.scopes):
                raise ToolError("Consent with 'net_get' scope required")
        url = args["url"]
        timeout = float(args.get("timeout", 20))
        r = requests.get(url, timeout=timeout)
        return {"url": url, "status": r.status_code, "headers": dict(r.headers), "text": r.text}

    def _fs_glob(self, args: Dict[str, Any], consent: Optional[fstool.ConsentToken]) -> Dict[str, Any]:
        pattern = args.get("pattern", "**/*")
        start = args.get("start", "/")
        return tool_glob(pattern=pattern, start=start, token=consent)

    def _fs_search(self, args: Dict[str, Any], consent: Optional[fstool.ConsentToken]) -> Dict[str, Any]:
        pattern = args["pattern"]
        path = args["path"]
        return tool_search(pattern=pattern, path=path, token=consent)

    def _shell_run(self, args: Dict[str, Any], consent: Optional[fstool.ConsentToken]) -> Dict[str, Any]:
        cmd = args["cmd"]
        workdir = args.get("workdir", "/")
        timeout = int(args.get("timeout", 120))
        return tool_shell(cmd=cmd, workdir=workdir, timeout=timeout, token=consent)

    def _git_status(self, args: Dict[str, Any], consent: Optional[fstool.ConsentToken]) -> Dict[str, Any]:
        workdir = args.get("workdir", "/")
        return tool_git_status(workdir=workdir, token=consent)

    def _git_add(self, args: Dict[str, Any], consent: Optional[fstool.ConsentToken]) -> Dict[str, Any]:
        workdir = args.get("workdir", "/")
        paths = args.get("paths", [])
        return tool_git_add(paths=paths, workdir=workdir, token=consent)

    def _git_commit(self, args: Dict[str, Any], consent: Optional[fstool.ConsentToken]) -> Dict[str, Any]:
        workdir = args.get("workdir", "/")
        message = args.get("message", "update")
        return tool_git_commit(message=message, workdir=workdir, token=consent)


# ------------------ Executor ------------------

class PlanExecutor:
    def __init__(self, db: Optional[MemoryDB] = None, registry: Optional[ToolRegistry] = None):
        self.db = db or MemoryDB()
        self.registry = registry or ToolRegistry()
        self.sem = asyncio.Semaphore(CONCURRENCY)

    def _emit(self, ev: PlanEvent):
        self.db.append_event(ev.dict())

    def _persist_plan(self, plan: Plan):
        self.db.upsert_plan(plan.dict())
        for s in plan.steps:
            row = s.dict()
            row["plan_id"] = plan.id
            row["max_retries"] = s.guard.max_retries
            self.db.upsert_step(row)

    async def _run_step(self, plan: Plan, step: Step, consent: Optional[fstool.ConsentToken]) -> None:
        step.attempts += 1
        step.mark_running()
        self._persist_plan(plan)
        self._emit(PlanEvent(type="step.started", plan_id=plan.id, step_id=step.id, payload={"attempt": step.attempts}))

        tool = self.registry.resolve(step.capability.name)
        # Consent: auto grant (dev) or validate provided token scopes
        if AUTO_CONSENT and fstool.REQUIRE_CONSENT:
            consent = fstool.ConsentToken(token="auto", scopes=["*"])
        elif fstool.REQUIRE_CONSENT and consent is None:
            raise ToolError("Consent required")

        # Retry loop with jitter
        backoff = step.guard.retry_backoff_ms
        jitter = step.guard.retry_backoff_jitter_ms
        last_err = None
        start = now_ms()
        for attempt in range(step.guard.max_retries + 1):
            try:
                out = tool["fn"](step.input, consent)
                step.mark_done(out)
                self._emit(PlanEvent(type="step.done", plan_id=plan.id, step_id=step.id, payload={"attempt": attempt, "output": out}))
                self._persist_plan(plan)
                return
            except Exception as e:  # noqa
                last_err = str(e)
                step.error = last_err
                if attempt >= step.guard.max_retries:
                    break
                # deadline check
                if step.guard.deadline_ms is not None and now_ms() - start > step.guard.deadline_ms:
                    break
                await asyncio.sleep((backoff + random.randint(0, jitter)) / 1000.0)

        step.mark_failed(last_err or "unknown_error")
        self._emit(PlanEvent(type="step.failed", plan_id=plan.id, step_id=step.id, payload={"error": step.error}))
        self._persist_plan(plan)

    async def run(self, plan: Plan, consent: Optional[fstool.ConsentToken] = None) -> Plan:
        if plan.state in (PlanState.DONE, PlanState.CANCELLED, PlanState.FAILED):
            return plan
        plan.state = PlanState.RUNNING
        self._persist_plan(plan)
        self._emit(PlanEvent(type="plan.started", plan_id=plan.id, payload={"title": plan.title}))

        # Basic DAG execution with limited concurrency
        pending: Dict[str, Step] = {s.id: s for s in plan.steps}
        while True:
            # Determine runnable
            completed = {s.id for s in plan.steps if s.state == StepState.DONE}
            failed = [s for s in plan.steps if s.state == StepState.FAILED]
            if failed:
                plan.state = PlanState.FAILED
                self._persist_plan(plan)
                self._emit(PlanEvent(type="plan.failed", plan_id=plan.id, payload={"failed_steps": [f.id for f in failed]}))
                return plan
            if plan.all_done():
                plan.state = PlanState.DONE
                self._persist_plan(plan)
                self._emit(PlanEvent(type="plan.done", plan_id=plan.id, payload={}))
                return plan

            runnable = [s for s in plan.runnable_steps() if s.id in pending]
            if not runnable:
                # No runnable but not done -> blocked wait
                await asyncio.sleep(0.05)
                continue

            tasks = []
            for s in runnable:
                pending.pop(s.id, None)
                await self.sem.acquire()
                tasks.append(asyncio.create_task(self._run_step(plan, s, consent)))
                # release semaphore on completion
                tasks[-1].add_done_callback(lambda _: self.sem.release())

            # Let at least one task progress
            await asyncio.sleep(0)

    # Convenience: run plan dict loaded from DB
    async def run_by_id(self, plan_id: str) -> Plan:
        row = self.db.get_plan(plan_id)
        if not row:
            raise RuntimeError(f"Plan {plan_id} not found")
        from packages.plan.olympus_plan.models import Plan as PydPlan, Step as PydStep  # avoid circulars
        steps_rows = self.db.get_steps(plan_id)
        steps = []
        for r in steps_rows:
            s = PydStep(
                id=r["id"],
                name=r["name"],
                capability=r["capability"],
                input=r["input"],
                deps=r["deps"],
                guard=r["guard"],
                state=r["state"],
                attempts=r["attempts"],
                started_at=r["started_at"],
                ended_at=r["ended_at"],
                error=r["error"],
                output=r["output"],
            )
            steps.append(s)
        plan = PydPlan(
            id=row["id"],
            title=row["title"],
            state=row["state"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            budget=row["budget"],
            steps=steps,
            metadata=row["metadata"],
        )
        return await self.run(plan)


# -------------- CLI entry (optional) --------------
if __name__ == "__main__":
    import argparse
    from packages.plan.olympus_plan.models import Plan, Step, CapabilityRef

    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-id", help="Existing plan id to run")
    args = parser.parse_args()

    db = MemoryDB()
    ex = PlanExecutor(db=db)

    async def main():
        if args.plan_id:
            await ex.run_by_id(args.plan_id)
            return
        # sample plan: write then read a file
        cap_write = CapabilityRef(name="fs.write", scope=[fstool.WRITE_SCOPE])
        cap_read = CapabilityRef(name="fs.read", scope=[fstool.READ_SCOPE])
        p = Plan(
            title="demo write+read",
            steps=[
                Step(name="write", capability=cap_write, input={"path": "demo/out.txt", "content": "hello"}),
                Step(name="read", capability=cap_read, input={"path": "demo/out.txt"}, deps=[]),
            ],
        )
        ex._persist_plan(p)
        await ex.run(p)

    asyncio.run(main())
