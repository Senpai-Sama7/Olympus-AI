import json
import logging
import sys
import time
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
			"path": request.url.path,
			"method": request.method,
			"status": resp.status_code,
			"duration_ms": duration_ms,
			"request_id": getattr(request.state, "request_id", None),
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
			}
			return json.dumps(entry)

	root = logging.getLogger()
	root.setLevel(level)
	for h in list(root.handlers):
		root.removeHandler(h)
	sh = logging.StreamHandler(sys.stdout)
	sh.setFormatter(JsonFormatter())
	root.addHandler(sh)
