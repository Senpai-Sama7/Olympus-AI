# app.py
import os, time, json, uuid, hashlib, random, threading
from typing import Callable, Optional, Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

# --------- Build/Config Sentinels ---------
GIT_SHA = os.getenv("GIT_SHA", "dev")
BUILD_ID = os.getenv("BUILD_ID", "local")
CONFIG_HASH = hashlib.sha1(json.dumps({
    k: os.getenv(k) for k in sorted(os.environ) if k.startswith("APP_")
}).encode()).hexdigest()[:12]

FEATURE_FLAGS = {
    "use_flaky_dep": os.getenv("APP_USE_FLAKY_DEP", "true").lower() == "true",
    "ask_before_doing": os.getenv("APP_ASK_BEFORE_DOING", "true").lower() == "true",
}

# --------- Simple JSON logger ---------
def log(level: str, msg: str, **fields):
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "level": level.upper(),
        "msg": msg,
        "git_sha": GIT_SHA,
        "build_id": BUILD_ID,
        "config_hash": CONFIG_HASH,
        **fields,
    }
    print(json.dumps(record, ensure_ascii=False))

def log_kv(level: str, msg: str, extras: Optional[Dict[str, Any]] = None, **fields):
    """Merge extras and fields safely to avoid duplicate kwargs."""
    merged = {}
    if extras:
        merged.update(extras)
    merged.update(fields)
    log(level, msg, **merged)

# --------- Prometheus metrics ---------
REG = CollectorRegistry()
REQUESTS = Counter("requests_total", "HTTP requests", ["route", "method", "code"], registry=REG)
ERRORS = Counter("errors_total", "Errors by class", ["route", "error_class"], registry=REG)
LATENCY = Histogram("request_duration_seconds", "Latency", ["route"], registry=REG,
                    buckets=(0.01,0.05,0.1,0.2,0.5,1,2,5,10))
CPU_SAT = Gauge("cpu_saturation", "CPU saturation (dummy)", registry=REG)
QUEUE_DEPTH = Gauge("queue_depth", "In-flight work items", registry=REG)
CIRCUIT_STATE = Gauge("circuit_open", "Circuit breaker 1=open,0=closed", registry=REG)
NULL_RATE = Gauge("data_null_rate", "Null rate for synthetic field", ["field"], registry=REG)

_inflight_lock = threading.Lock()
_inflight = 0
def inc_inflight():
    global _inflight
    with _inflight_lock:
        _inflight += 1
        QUEUE_DEPTH.set(_inflight)
def dec_inflight():
    global _inflight
    with _inflight_lock:
        _inflight -= 1
        QUEUE_DEPTH.set(max(0, _inflight))

# --------- Middleware: correlation + RED ---------
class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        route = request.url.path
        method = request.method
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        start = time.time()
        inc_inflight()
        status_code = 200
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            return response
        except HTTPException as e:
            status_code = e.status_code
            raise
        except Exception:
            status_code = 500
            raise
        finally:
            dur = time.time() - start
            LATENCY.labels(route=route).observe(dur)
            REQUESTS.labels(route=route, method=method, code=str(status_code)).inc()
            log("info", "request_done",
                route=route, method=method, code=status_code, duration_ms=int(dur*1000),
                correlation_id=correlation_id, feature_flags=FEATURE_FLAGS)
            dec_inflight()

app = FastAPI(title="Debuggable Service")
app.add_middleware(ObservabilityMiddleware)

# --------- Invariants & helpers ---------
class InvariantError(Exception): ...
def get_cid(request: Request) -> str:
    return getattr(request.state, "correlation_id", None) or \
           request.headers.get("x-correlation-id") or "n/a"

def fail_invariant(request: Request, code: str, detail: str, extras: Dict[str,Any]):
    route = request.url.path
    cid = get_cid(request)
    ERRORS.labels(route=route, error_class=code).inc()
    # SAFE: merged once, no duplicate kwargs
    log_kv("error", "invariant_failed", extras,
           sentinel_code=code, detail=detail, correlation_id=cid)
    return JSONResponse(status_code=400, content={
        "sentinel": code,
        "msg": detail,
        "correlation_id": cid
    })

# --------- Fake flaky dependency with a circuit breaker ---------
circuit_open = False
circuit_reset_at = 0

def flaky_dependency(correlation_id: str) -> str:
    global circuit_open, circuit_reset_at
    now = time.time()
    if circuit_open and now < circuit_reset_at:
        CIRCUIT_STATE.set(1)
        raise RuntimeError("CIRCUIT_OPEN")
    CIRCUIT_STATE.set(0)
    # 20% failure to simulate flakiness
    if random.random() < 0.2:
        circuit_open = True
        circuit_reset_at = now + 5  # open 5s
        raise RuntimeError("FLAKY_DEP_FAIL")
    return "OK"

# --------- Routes ---------
@app.get("/healthz")
def healthz():
    return {"status": "ready", "dep": "ok", "git_sha": GIT_SHA, "config_hash": CONFIG_HASH}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(REG), media_type=CONTENT_TYPE_LATEST)

@app.get("/compute")
def compute(x: Optional[int] = 1, request: Request = None):
    route = "/compute"
    cid = get_cid(request)

    # Input invariant: x must be positive int < 1e6 -> return JSON 400
    if not (isinstance(x, int) and 0 < x < 1_000_000):
        return fail_invariant(request, "OLY-CMP-001",
                              "x must be a positive integer < 1e6",
                              {"route": route, "x": x})

    # Data drift sentinel (toy): if x==13, flag suspicious
    NULL_RATE.labels(field="foo").set(0.0)
    if x == 13:
        log("warn", "suspicious_value", route=route, correlation_id=cid, x=x)

    # Fake work + flaky dep
    start = time.time()
    try:
        if FEATURE_FLAGS["use_flaky_dep"]:
            flaky_dependency(cid)
        result = x * 2
        duration_ms = int((time.time() - start) * 1000)
        log("info", "compute_done", route=route, correlation_id=cid,
            input=x, output=result, duration_ms=duration_ms)
        return {"ok": True, "input": x, "output": result, "duration_ms": duration_ms,
                "correlation_id": cid, "git_sha": GIT_SHA}
    except Exception as e:
        ERRORS.labels(route=route, error_class=type(e).__name__).inc()
        log("error", "compute_failed", route=route, correlation_id=cid,
            sentinel_code="OLY-CMP-500", error=str(e))
        raise HTTPException(status_code=503, detail={
            "sentinel": "OLY-CMP-500",
            "err": str(e),
            "correlation_id": cid
        })

@app.post("/act")
def act(request: Request, body: Dict[str, Any]):
    route = "/act"
    cid = get_cid(request)
    action = body.get("action", "")
    if FEATURE_FLAGS["ask_before_doing"]:
        log("info", "action_requires_consent", route=route, correlation_id=cid, action=action)
        raise HTTPException(status_code=403, detail={
            "sentinel":"OLY-ACT-401","msg":"Consent required","correlation_id": cid})
    log("info", "action_performed", route=route, correlation_id=cid, action=action)
    return {"ok": True, "action": action, "correlation_id": cid}

