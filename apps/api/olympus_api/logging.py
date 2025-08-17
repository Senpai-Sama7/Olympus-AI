import json
import logging
import sys
import time
import os
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JsonRequestLogger(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, component: str) -> None:
        super().__init__(app)
        self.component = component

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        resp = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)
        entry = {
            "timestamp": _utc_iso(),
            "level": "INFO",
            "message": "access",
            "component": self.component,
            "route": request.url.path,
            "sentinel": os.environ.get("SENTINEL"),
            "correlation_id": getattr(request.state, "request_id", None),
            "git_sha": os.environ.get("GIT_SHA"),
            "config_hash": os.environ.get("CONFIG_HASH"),
            "method": request.method,
            "status": resp.status_code,
            "duration_ms": duration_ms,
        }
        print(json.dumps(entry), file=sys.stdout)
        return resp


def configure_json_logging(component: str, level: str = "INFO") -> None:
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            entry = {
                "timestamp": _utc_iso(),
                "level": record.levelname,
                "message": record.getMessage(),
                "component": component,
                "sentinel": os.environ.get("SENTINEL"),
                "git_sha": os.environ.get("GIT_SHA"),
                "config_hash": os.environ.get("CONFIG_HASH"),
            }
            return json.dumps(entry)

    log_level = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(log_level)
    for h in list(root.handlers):
        root.removeHandler(h)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(JsonFormatter())
    root.addHandler(sh)