import asyncio
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .cors import build_cors_kwargs
from .logging import JsonRequestLogger, configure_json_logging
from .metrics import request_duration_seconds, requests_total
from .metrics import router as metrics_router
from .middleware import (
    BodySizeLimitMiddleware,
    RequestIDMiddleware,
    TimeoutMiddleware,
    TokenBucketLimiter,
)
from .settings import get_settings

settings = get_settings()

app = FastAPI(title="Olympus API", version="0.1.0")

# Logging
configure_json_logging(component="api", level=settings.LOG_LEVEL)

# CORS
app.add_middleware(CORSMiddleware, **build_cors_kwargs(settings))

# Request ID
app.add_middleware(RequestIDMiddleware)

# Body size
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.MAX_BODY_BYTES)

# Rate limiting
app.add_middleware(TokenBucketLimiter, settings=settings)

# Timeout
app.add_middleware(
    TimeoutMiddleware,
    connect_timeout=settings.CONNECT_TIMEOUT_SEC,
    request_timeout=settings.REQUEST_TIMEOUT_SEC,
)

# Access logs
app.add_middleware(JsonRequestLogger, component="api")

# Metrics route (enabled)
if settings.METRICS_ENABLED:
    app.include_router(metrics_router)

# Plans router
from . import plans
app.include_router(plans.router)


@app.middleware("http")
async def _metrics_middleware(request: Request, call_next):
    path = request.url.path
    method = request.method
    with request_duration_seconds.labels(
        path=path, method=method, status="_pending"
    ).time():
        response = await call_next(request)
        requests_total.labels(
            path=path, method=method, status=str(response.status_code)
        ).inc()
        return response


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/ping")
async def ping() -> Dict[str, str]:
    return {"message": "pong"}


@app.get("/v1/config")
async def config_preview() -> Dict[str, object]:
    return settings.as_redacted_dict()


# Dev-only slow endpoint for timeout tests
@app.get("/v1/dev/sleep")
async def dev_sleep(sec: float = 0.0) -> Dict[str, str]:
    if settings.ENV == "prod":
        return {"message": "disabled"}
    await asyncio.sleep(max(0.0, sec))
    return {"message": "ok"}
