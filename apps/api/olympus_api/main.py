# apps/api/olympus_api/main.py
from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, CollectorRegistry, generate_latest
from pydantic import BaseModel, Field
import requests

from packages.memory.olympus_memory.db import MemoryDB
from packages.plan.olympus_plan.models import CapabilityRef, Guard, Plan, PlanEvent, PlanState, Step, StepState
from apps.worker.olympus_worker.main import PlanExecutor
from packages.tools.olympus_tools.fs import ConsentToken
from .settings import get_settings
from .middleware import BodySizeLimitMiddleware, RequestIDMiddleware, TimeoutMiddleware, TokenBucketLimiter
from .cors import build_cors_kwargs
import asyncio

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
REQUESTS = Counter("requests_total", "HTTP requests", ["route", "method", "code"], registry=REG)
ERRORS = Counter("errors_total", "Errors by class", ["route", "error_class"], registry=REG)
LAT = Histogram("request_duration_seconds", "Latency", ["route"], registry=REG,
                buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10))
CIRCUIT = Gauge("circuit_open", "Breaker (compat)", registry=REG)
QUEUE_DEPTH = Gauge("queue_depth", "In-flight requests", registry=REG)

# ---------- App ----------
app = FastAPI(title=APP_NAME)

# Settings-driven CORS and core middlewares
_settings = get_settings()
app.add_middleware(CORSMiddleware, **build_cors_kwargs(_settings))
app.add_middleware(RequestIDMiddleware)
app.add_middleware(TimeoutMiddleware, connect_timeout=_settings.CONNECT_TIMEOUT_SEC, request_timeout=_settings.REQUEST_TIMEOUT_SEC)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=_settings.MAX_BODY_BYTES)
app.add_middleware(TokenBucketLimiter, settings=_settings)

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
    except Exception as e:
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

# ---------- Routes ----------

@app.get("/healthz")
def healthz():
    return {"status": "ready", "ask_before_doing": ASK_BEFORE_DOING}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return JSONResponse(generate_latest(REG), media_type=CONTENT_TYPE_LATEST)


@app.get("/v1/config")
def config_echo():
    cfg = get_settings().as_redacted_dict()
    # Attach a lightweight LLM usage snapshot
    try:
        today = time.strftime("%Y-%m-%d", time.gmtime())
        db = DB  # reuse
        usd = db.cache_get(f"budget:{today}") or {"value": {"usd": 0.0}}
        toks = db.cache_get(f"budget_tokens:{today}") or {"value": {"tokens": 0}}
        cfg["LLM_USAGE_TODAY"] = {"usd": float(usd["value"].get("usd", 0.0)), "tokens": int(toks["value"].get("tokens", 0))}
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
            return {"backend": "llamacpp", "url": s.LLAMA_CPP_URL, "ok": ok, "status": r.status_code}
        else:
            r = requests.get(f"{s.OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=2.0)
            ok = r.status_code == 200
            return {"backend": "ollama", "url": s.OLLAMA_BASE_URL, "ok": ok, "status": r.status_code}
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
def submit_plan(body: SubmitPlan):
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
    DB.append_event(PlanEvent(type="plan.created", plan_id=p.id, payload={"title": p.title}).dict())
    return {"plan_id": p.id, "state": p.state, "steps": [s.id for s in p.steps]}


@app.get("/v1/plan/{plan_id}")
def get_plan(plan_id: str):
    row = DB.get_plan(plan_id)
    if not row:
        raise HTTPException(status_code=404, detail="plan not found")
    steps = DB.get_steps(plan_id)
    return {"plan": row, "steps": steps, "events": list(DB.events_for_plan(plan_id))}


@app.post("/v1/plan/{plan_id}/run")
async def run_plan(plan_id: str, background: BackgroundTasks):
    # Execute asynchronously
    background.add_task(EXECUTOR.run_by_id, plan_id)
    return {"ok": True, "plan_id": plan_id}


class ActBody(BaseModel):
    capability: str
    input: Dict[str, Any]
    consent_token: Optional[str] = None
    consent_scopes: Optional[List[str]] = None


@app.post("/v1/act")
def act(body: ActBody):
    """
    Direct capability execution with explicit consent (bypasses planning).
    """
    if ASK_BEFORE_DOING and not body.consent_token:
        raise HTTPException(status_code=403, detail={"sentinel": "OLY-ACT-401", "msg": "Consent required"})

    consent = ConsentToken(token=body.consent_token or "explicit", scopes=body.consent_scopes or ["*"])
    # Use the same registry the worker uses
    tool = EXECUTOR.registry.resolve(body.capability)
    try:
        out = tool["fn"](body.input, consent)
        return {"ok": True, "output": out}
    except Exception as e:
        ERRORS.labels(route="/v1/act", error_class=type(e).__name__).inc()
        raise HTTPException(status_code=400, detail={"sentinel": "OLY-ACT-400", "err": str(e)})


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
