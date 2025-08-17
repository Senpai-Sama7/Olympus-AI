#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
from typing import Optional

import httpx


API = "http://127.0.0.1:8000"


def submit_plan(plan_path: str) -> str:
    with open(plan_path, "r", encoding="utf-8") as f:
        body = json.load(f)
    r = httpx.post(f"{API}/v1/plan/submit", json=body, timeout=30)
    r.raise_for_status()
    return r.json()["plan_id"]


def run_plan(plan_id: str) -> None:
    r = httpx.post(f"{API}/v1/plan/{plan_id}/run", timeout=10)
    r.raise_for_status()


def wait(plan_id: str, timeout_s: int = 60) -> str:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = httpx.get(f"{API}/v1/plan/{plan_id}", timeout=10)
        r.raise_for_status()
        data = r.json()
        state = data["plan"]["state"]
        if state in ("DONE", "FAILED", "CANCELLED"):
            return state
        time.sleep(0.5)
    return "TIMEOUT"


def agent_execute(goal: str) -> str:
    r = httpx.post(f"{API}/v1/agent/execute", json={"goal": goal}, timeout=30)
    r.raise_for_status()
    return r.json()["plan_id"]


def main(argv):
    if len(argv) < 2:
        print("usage: agent_cli.py [submit <plan.json> | run <plan_id> | wait <plan_id> [timeout] | agent <goal...>]")
        sys.exit(2)
    cmd = argv[1]
    if cmd == "submit":
        pid = submit_plan(argv[2])
        print(pid)
    elif cmd == "run":
        run_plan(argv[2])
        print("ok")
    elif cmd == "wait":
        st = wait(argv[2], int(argv[3]) if len(argv) > 3 else 60)
        print(st)
    elif cmd == "agent":
        goal = " ".join(argv[2:])
        pid = agent_execute(goal)
        run_plan(pid)
        st = wait(pid)
        print(st)
    else:
        print("unknown cmd")
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv)
