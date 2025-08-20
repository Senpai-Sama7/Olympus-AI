# apps/api/olympus_api/main.py
from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    CollectorRegistry,
    generate_latest,
)
from pydantic import BaseModel, Field
import requests
from fastapi.responses import StreamingResponse

from packages.memory.olympus_memory.db import MemoryDB
from packages.plan.olympus_plan.models import (
    CapabilityRef,
    Guard,
    Plan,
    PlanEvent,
    PlanState,
    Step,
)
from apps.worker.olympus_worker.main import PlanExecutor
from packages.tools.olympus_tools.fs import ConsentToken
from .settings import get_settings
from .middleware import (
    BodySizeLimitMiddleware,
    RequestIDMiddleware,
    TimeoutMiddleware,
    TokenBucketLimiter,
)
from .cors import build_cors_kwargs
import asyncio
from packages.llm.olympus_llm.router import LLMRouter
from .auth import get_current_user
from .planner import propose_plan, reflect_and_revise
from .nl_agent import handle_chat_turn

APP_NAME = "Olympus API"
ASK_BEFORE_DOING = os.getenv("APP_ASK_BEFORE_DOING", "true").lower() == "true"


# ---------- Logging ----------
def log(level: str, msg: str, **fields):
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "level": level.upper(),
        "msg": msg,
        **fields,
    }
    print(json.dumps(rec, ensure_ascii=False))


# ---------- Metrics ----------
REG = CollectorRegistry()
REQUESTS = Counter(
    "requests_total", "HTTP requests", ["route", "method", "code"], registry=REG
)
ERRORS = Counter(
    "errors_total", "Errors by class", ["route", "error_class"], registry=REG
)
LAT = Histogram(
    "request_duration_seconds",
    "Latency",
    ["route"],
    registry=REG,
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10),
)
CIRCUIT = Gauge("circuit_open", "Breaker (compat)", registry=REG)
QUEUE_DEPTH = Gauge("queue_depth", "In-flight requests", registry=REG)

# ---------- App ----------
app = FastAPI(title=APP_NAME)

# Settings-driven CORS and core middlewares
_settings = get_settings()
app.add_middleware(CORSMiddleware, **build_cors_kwargs(_settings))
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    TimeoutMiddleware,
    connect_timeout=_settings.CONNECT_TIMEOUT_SEC,
    request_timeout=_settings.REQUEST_TIMEOUT_SEC,
)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=_settings.MAX_BODY_BYTES)
app.add_middleware(TokenBucketLimiter, settings=_settings)

# Static UI (optional)
try:
    app.mount("/ui", StaticFiles(directory="public", html=True), name="ui")
except Exception:
    pass


# ---------- Middleware ----------
@app.middleware("http")
async def obs_mw(request: Request, call_next):
    route = request.url.path
    method = request.method
    start = time.time()
    try:
        resp = await call_next(request)
        code = resp.status_code
        return resp
    except HTTPException as e:
        code = e.status_code
        raise
    except Exception:
        code = 500
        raise
    finally:
        dur = time.time() - start
        LAT.labels(route=route).observe(dur)
        REQUESTS.labels(route=route, method=method, code=str(code)).inc()
        QUEUE_DEPTH.set(0)


# ---------- Models ----------
class SubmitStep(BaseModel):
    name: str
    capability: str
    input: Dict[str, Any] = Field(default_factory=dict)
    deps: List[str] = Field(default_factory=list)
    guard: Guard = Field(default_factory=Guard)


class SubmitPlan(BaseModel):
    title: str
    steps: List[SubmitStep]
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------- State ----------
DB = MemoryDB()
EXECUTOR = PlanExecutor(db=DB)
ROUTER = LLMRouter()

# ---------- Routes ----------


@app.get("/healthz")
def healthz():
    return {"status": "ready", "ask_before_doing": ASK_BEFORE_DOING}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(REG), media_type=CONTENT_TYPE_LATEST)


@app.get("/v1/config")
def config_echo():
    cfg = get_settings().as_redacted_dict()
    # Attach a lightweight LLM usage snapshot
    try:
        today = time.strftime("%Y-%m-%d", time.gmtime())
        db = DB  # reuse
        usd = db.cache_get(f"budget:{today}") or {"value": {"usd": 0.0}}
        toks = db.cache_get(f"budget_tokens:{today}") or {"value": {"tokens": 0}}
        cfg["LLM_USAGE_TODAY"] = {
            "usd": float(usd["value"].get("usd", 0.0)),
            "tokens": int(toks["value"].get("tokens", 0)),
        }
    except Exception:
        cfg["LLM_USAGE_TODAY"] = {"usd": 0.0, "tokens": 0}
    return cfg


@app.get("/v1/dev/sleep")
async def dev_sleep(sec: int = 0):
    sec = max(0, int(sec))
    await asyncio.sleep(sec)
    return {"ok": True, "slept": sec}


@app.post("/v1/dev/sleep")
async def dev_sleep_post():
    # Body size limits are enforced by middleware
    return {"ok": True}


@app.get("/v1/llm/health")
def llm_health():
    s = get_settings()
    try:
        if s.OLY_LLM_BACKEND.lower() in ("llamacpp", "llama.cpp"):
            r = requests.get(f"{s.LLAMA_CPP_URL.rstrip('/')}/health", timeout=2.0)
            ok = r.status_code == 200
            return {
                "backend": "llamacpp",
                "url": s.LLAMA_CPP_URL,
                "ok": ok,
                "status": r.status_code,
            }
        else:
            r = requests.get(f"{s.OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=2.0)
            ok = r.status_code == 200
            return {
                "backend": "ollama",
                "url": s.OLLAMA_BASE_URL,
                "ok": ok,
                "status": r.status_code,
            }
    except Exception as e:
        return {"ok": False, "error": str(e), "backend": s.OLY_LLM_BACKEND}


@app.get("/v1/llm/usage")
def llm_usage():
    today = time.strftime("%Y-%m-%d", time.gmtime())
    usd = DB.cache_get(f"budget:{today}") or {"value": {"usd": 0.0}}
    toks = DB.cache_get(f"budget_tokens:{today}") or {"value": {"tokens": 0}}
    return {
        "date": today,
        "usd": float(usd["value"].get("usd", 0.0)),
        "tokens": int(toks["value"].get("tokens", 0)),
    }


@app.post("/v1/plan/submit")
def submit_plan(body: SubmitPlan, user: Dict = Depends(get_current_user)):
    # materialize plan
    steps: List[Step] = []
    id_map: Dict[int, str] = {}
    for i, st in enumerate(body.steps):
        sid = str(uuid.uuid4())
        id_map[i] = sid
        steps.append(
            Step(
                id=sid,
                name=st.name,
                capability=CapabilityRef(name=st.capability, scope=[]),
                input=st.input,
                deps=[],
                guard=st.guard,
            )
        )
    # remap deps if user used indices
    for i, st in enumerate(body.steps):
        deps = []
        for dep in st.deps:
            # accept either a literal step id or an index string like "0"
            if dep in id_map.values():
                deps.append(dep)
            else:
                try:
                    deps.append(id_map[int(dep)])
                except Exception:
                    deps.append(dep)
        steps[i].deps = deps

    p = Plan(title=body.title, steps=steps, metadata=body.metadata)
    DB.upsert_plan(p.dict())
    for s in p.steps:
        row = s.dict()
        row["plan_id"] = p.id
        row["max_retries"] = s.guard.max_retries
        DB.upsert_step(row)
    DB.append_event(
        PlanEvent(type="plan.created", plan_id=p.id, payload={"title": p.title}).dict()
    )
    return {"plan_id": p.id, "state": p.state, "steps": [s.id for s in p.steps]}


@app.get("/v1/plan/{plan_id}")
def get_plan(plan_id: str, user: Dict = Depends(get_current_user)):
    row = DB.get_plan(plan_id)
    if not row:
        raise HTTPException(status_code=404, detail="plan not found")
    steps = DB.get_steps(plan_id)
    return {"plan": row, "steps": steps, "events": list(DB.events_for_plan(plan_id))}


class RunBody(BaseModel):
    consent_token: Optional[str] = None
    consent_scopes: Optional[List[str]] = None


@app.post("/v1/plan/{plan_id}/run")
async def run_plan(
    plan_id: str,
    background: BackgroundTasks,
    body: RunBody | None = None,
    user: Dict = Depends(get_current_user),
):
    # Execute asynchronously
    consent = None
    if body and (body.consent_token or body.consent_scopes):
        consent = ConsentToken(
            token=body.consent_token or "user", scopes=body.consent_scopes or []
        )
    (
        background.add_task(EXECUTOR.run_by_id, plan_id)
        if consent is None
        else background.add_task(EXECUTOR.run_by_id_with_consent, plan_id, consent)
    )
    return {"ok": True, "plan_id": plan_id}


class ActBody(BaseModel):
    capability: str
    input: Dict[str, Any]
    consent_token: Optional[str] = None
    consent_scopes: Optional[List[str]] = None


@app.post("/v1/act")
def act(body: ActBody, user: Dict = Depends(get_current_user)):
    """
    Direct capability execution with explicit consent (bypasses planning).
    """
    if ASK_BEFORE_DOING and not body.consent_token:
        raise HTTPException(
            status_code=403,
            detail={"sentinel": "OLY-ACT-401", "msg": "Consent required"},
        )

    consent = ConsentToken(
        token=body.consent_token or "explicit", scopes=body.consent_scopes or ["*"]
    )
    # Use the same registry the worker uses
    tool = EXECUTOR.registry.resolve(body.capability)
    try:
        out = tool["fn"](body.input, consent)
        return {"ok": True, "output": out}
    except Exception as e:
        ERRORS.labels(route="/v1/act", error_class=type(e).__name__).inc()
        raise HTTPException(
            status_code=400, detail={"sentinel": "OLY-ACT-400", "err": str(e)}
        )


class AgentExecuteBody(BaseModel):
    goal: str
    repo: Optional[str] = None
    consent_token: Optional[str] = None
    consent_scopes: Optional[List[str]] = None
    max_tokens: Optional[int] = 800
    max_iterations: int = 2
    model: Optional[str] = None


@app.post("/v1/agent/execute")
async def agent_execute(body: AgentExecuteBody, user: Dict = Depends(get_current_user)):
    """LLM-driven planner with reflection loop.
    1) Propose plan via LLM based on goal.
    2) Persist and run.
    3) If failed, summarize failure, ask LLM to revise plan, and retry up to max_iterations.
    """
    consent = None
    if body.consent_token or body.consent_scopes:
        consent = ConsentToken(
            token=body.consent_token or "user", scopes=body.consent_scopes or []
        )

    # Step 1: propose plan
    plan = propose_plan(
        goal=body.goal,
        router=ROUTER,
        context=None,
        model=body.model,
        temperature=0.2,
        max_tokens=body.max_tokens,
    )
    # Persist
    DB.upsert_plan(plan.dict())
    for s in plan.steps:
        row = s.dict()
        row["plan_id"] = plan.id
        row["max_retries"] = s.guard.max_retries
        DB.upsert_step(row)
    DB.append_event(
        PlanEvent(
            type="plan.created",
            plan_id=plan.id,
            payload={"title": plan.title, "goal": body.goal},
        ).dict()
    )

    # Execute + reflect loop
    max_iter = max(0, int(body.max_iterations))
    for i in range(max_iter + 1):
        # Run
        await EXECUTOR.run(plan, consent=consent)
        if plan.state == PlanState.DONE:
            return {
                "plan_id": plan.id,
                "state": plan.state,
                "iterations": i,
                "revised": False if i == 0 else True,
            }
        # If failed and we can iterate, reflect & revise
        if plan.state == PlanState.FAILED and i < max_iter:
            # summarize failure
            failed_steps = [
                {
                    "id": s.id,
                    "name": s.name,
                    "capability": s.capability.name,
                    "error": s.error,
                }
                for s in plan.steps
                if s.error
            ]
            failure = {"failed_steps": failed_steps}
            revised = reflect_and_revise(
                goal=body.goal,
                prev_plan=plan,
                failure=failure,
                router=ROUTER,
                model=body.model,
            )
            # overwrite plan (new id)
            plan = revised
            DB.upsert_plan(plan.dict())
            for s in plan.steps:
                row = s.dict()
                row["plan_id"] = plan.id
                row["max_retries"] = s.guard.max_retries
                DB.upsert_step(row)
            DB.append_event(
                PlanEvent(
                    type="plan.created",
                    plan_id=plan.id,
                    payload={"title": plan.title, "goal": body.goal, "rev": i + 1},
                ).dict()
            )
            # link parent and child via events
            DB.append_event(
                PlanEvent(
                    type="plan.revised",
                    plan_id=plan.id,
                    payload={
                        "parent_plan_id": failure.get("plan_id", ""),
                        "failure": failure,
                    },
                ).dict()
            )
            DB.append_event(
                PlanEvent(
                    type="plan.revised_to",
                    plan_id=failure.get("plan_id", plan.id),
                    payload={"child_plan_id": plan.id},
                ).dict()
            )
            continue
        break
    return {"plan_id": plan.id, "state": plan.state, "iterations": i, "revised": i > 0}


def build_failure_summary(plan_id: str) -> Dict[str, Any]:
    # Collect failed steps, error messages, and recent event payloads
    summary: Dict[str, Any] = {"plan_id": plan_id, "failed_steps": []}
    steps = DB.get_steps(plan_id)
    events = list(DB.events_for_plan(plan_id))
    events_by_step: Dict[str, List[Dict[str, Any]]] = {}
    for ev in events:
        sid = ev.get("step_id")
        if sid:
            events_by_step.setdefault(sid, []).append(ev)
    for s in steps:
        if s.get("state") == "FAILED":
            sid = s["id"]
            recents = [e for e in events_by_step.get(sid, [])][-5:]
            previews: Dict[str, Any] = {}
            out = s.get("output") or {}
            for k in ("stdout", "stderr", "text", "content"):
                v = out.get(k)
                if isinstance(v, str) and v:
                    previews[k] = v[:512] + ("..." if len(v) > 512 else "")
            summary["failed_steps"].append(
                {
                    "id": sid,
                    "name": s.get("name"),
                    "capability": (s.get("capability") or {}).get("name"),
                    "error": s.get("error"),
                    "recent_events": [
                        {
                            "type": e.get("type"),
                            "ts": e.get("ts"),
                            "payload": e.get("payload"),
                        }
                        for e in recents
                    ],
                    "output_preview": previews,
                }
            )
    return summary


class ChatBody(BaseModel):
    messages: List[Dict[str, str]]
    model: Optional[str] = None
    temperature: float = 0.2
    max_tokens: Optional[int] = 800


@app.post("/v1/chat/stream")
def chat_stream(body: ChatBody, user: Dict = Depends(get_current_user)):
    async def gen():
        try:
            async for chunk in ROUTER.stream_chat(
                messages=body.messages, model=body.model, temperature=body.temperature
            ):
                yield chunk
        except Exception as e:
            yield f"[error] {type(e).__name__}: {e}"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/v1/chat/{session_id}/history")
def chat_history(session_id: str, user: Dict = Depends(get_current_user)):
    # Return chat.* events for this session id (we use session_id as plan_id key for chat logs)
    events = [
        {
            "ts": ev.get("ts"),
            "type": ev.get("type"),
            "payload": ev.get("payload"),
        }
        for ev in DB.events_for_plan(session_id)
        if str(ev.get("type", "")).startswith("chat.")
    ]
    return {"session_id": session_id, "events": events}


@app.get("/v1/plan/{plan_id}/summary")
def plan_summary(plan_id: str, user: Dict = Depends(get_current_user)):
    row = DB.get_plan(plan_id)
    if not row:
        raise HTTPException(status_code=404, detail="plan not found")
    steps = DB.get_steps(plan_id)
    simple = []
    for s in steps:
        cap = (s.get("capability") or {}).get("name")
        out = s.get("output") or {}
        preview = {}
        for k in ("stdout", "stderr", "text", "content"):
            v = out.get(k)
            if isinstance(v, str) and v:
                preview[k] = v[:256] + ("..." if len(v) > 256 else "")
        simple.append(
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "capability": cap,
                "deps": s.get("deps", []),
                "state": s.get("state"),
                "error": s.get("error"),
                "output_preview": preview,
            }
        )
    return {
        "plan_id": plan_id,
        "title": row.get("title"),
        "state": row.get("state"),
        "steps": simple,
    }


class NLBody(BaseModel):
    message: str
    session_id: Optional[str] = None
    consent_token: Optional[str] = None
    consent_scopes: Optional[List[str]] = None
    max_tokens: Optional[int] = 800
    auto_escalate: Optional[bool] = None


@app.post("/v1/agent/chat")
async def agent_chat(body: NLBody, user: Dict = Depends(get_current_user)):
    allowed_scopes = body.consent_scopes if body.consent_scopes else None
    reply, plan = await handle_chat_turn(
        user_text=body.message,
        router=ROUTER,
        allowed_scopes=allowed_scopes,
        consent_token=body.consent_token,
        max_tokens=body.max_tokens,
    )
    # Persist chat turn as events
    sess = body.session_id or str(uuid.uuid4())
    DB.append_event(
        PlanEvent(type="chat.user", plan_id=sess, payload={"text": body.message}).dict()
    )
    DB.append_event(
        PlanEvent(type="chat.assistant", plan_id=sess, payload={"reply": reply}).dict()
    )
    result = {"session_id": sess, **reply}
    if plan is not None and not reply.get("requires_consent"):
        # persist plan and run
        DB.upsert_plan(plan.dict())
        for s in plan.steps:
            row = s.dict()
            row["plan_id"] = plan.id
            row["max_retries"] = s.guard.max_retries
            DB.upsert_step(row)
        DB.append_event(
            PlanEvent(
                type="plan.created",
                plan_id=plan.id,
                payload={"title": plan.title, "goal": body.message, "session_id": sess},
            ).dict()
        )
        # Heuristic: escalate to reflection loop for complex goals
        complex_goal = any(
            k in body.message.lower()
            for k in ("migrate", "refactor", "type-check", "lint", "test", "deploy")
        )
        if (body.auto_escalate is True) or (
            body.auto_escalate is None and complex_goal
        ):
            consent = None
            if body.consent_token or (allowed_scopes and "*" not in allowed_scopes):
                consent = ConsentToken(
                    token=body.consent_token or "user", scopes=allowed_scopes or ["*"]
                )
            DB.upsert_plan(plan.dict())
            for s in plan.steps:
                row = s.dict()
                row["plan_id"] = plan.id
                row["max_retries"] = s.guard.max_retries
                DB.upsert_step(row)
            DB.append_event(
                PlanEvent(
                    type="plan.created",
                    plan_id=plan.id,
                    payload={
                        "title": plan.title,
                        "goal": body.message,
                        "session_id": sess,
                    },
                ).dict()
            )
            cur = plan
            for i in range(2 + 1):
                await EXECUTOR.run(cur, consent=consent)
                if cur.state == PlanState.DONE:
                    result.update(
                        {"plan_id": cur.id, "state": cur.state, "iterations": i}
                    )
                    break
                if cur.state == PlanState.FAILED and i < 2:
                    failure = build_failure_summary(cur.id)
                    revised = reflect_and_revise(
                        goal=body.message,
                        prev_plan=cur,
                        failure=failure,
                        router=ROUTER,
                        model=None,
                    )
                    DB.upsert_plan(revised.dict())
                    for s in revised.steps:
                        row = s.dict()
                        row["plan_id"] = revised.id
                        row["max_retries"] = s.guard.max_retries
                        DB.upsert_step(row)
                    DB.append_event(
                        PlanEvent(
                            type="plan.created",
                            plan_id=revised.id,
                            payload={
                                "title": revised.title,
                                "goal": body.message,
                                "session_id": sess,
                                "rev": i + 1,
                            },
                        ).dict()
                    )
                    cur = revised
                    continue
                result.update({"plan_id": cur.id, "state": cur.state, "iterations": i})
                break
        else:
            DB.upsert_plan(plan.dict())
            for s in plan.steps:
                row = s.dict()
                row["plan_id"] = plan.id
                row["max_retries"] = s.guard.max_retries
                DB.upsert_step(row)
            DB.append_event(
                PlanEvent(
                    type="plan.created",
                    plan_id=plan.id,
                    payload={
                        "title": plan.title,
                        "goal": body.message,
                        "session_id": sess,
                    },
                ).dict()
            )
            await EXECUTOR.run(plan)
            result.update({"plan_id": plan.id, "state": plan.state})
    return result


# ---------- Example curl (for humans) ----------
# Submit+Run:
# curl -sS -X POST localhost:8000/v1/plan/submit -H 'content-type: application/json' -d '{ \
#   "title":"write then read", \
#   "steps":[ \
#     {"name":"w","capability":"fs.write","input":{"path":"demo/api.txt","content":"hi"}}, \
#     {"name":"r","capability":"fs.read","deps":["0"],"input":{"path":"demo/api.txt"}} \
#   ] \
# }' | jq .
# curl -sS -X POST localhost:8000/v1/plan/<PLAN_ID>/run | jq .


@app.get("/v1/agent/{plan_id}/trace")
def agent_trace(plan_id: str, user: Dict = Depends(get_current_user)):
    # Traverse revision chain via events across parent/child links
    visited = set()
    chain = []
    cur = plan_id
    while cur and cur not in visited:
        visited.add(cur)
        plan = DB.get_plan(cur)
        if not plan:
            break
        chain.append(
            {"plan_id": cur, "title": plan.get("title"), "state": plan.get("state")}
        )
        next_id = None
        for ev in DB.events_for_plan(cur):
            if ev.get("type") == "plan.revised_to":
                next_id = (ev.get("payload") or {}).get("child_plan_id")
        cur = next_id
    revisions = []
    for node in chain:
        pid = node["plan_id"]
        revs = [
            {"plan_id": pid, "failure": (ev.get("payload") or {}).get("failure")}
            for ev in DB.events_for_plan(pid)
            if ev.get("type") == "plan.revised"
        ]
    return {"chain": chain, "revisions": revisions}
