import asyncio
import os
import time
import uuid
from collections import defaultdict
from typing import Awaitable, Callable, Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .settings import Settings


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Allow dynamic override via env for tests
        max_bytes = int(os.getenv("MAX_BODY_BYTES", str(self.max_bytes)))
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > max_bytes:
            return Response(
                content='{"error":"payload too large"}',
                media_type="application/json",
                status_code=413,
            )

        # Wrap receive to enforce size for unknown Content-Length
        received = 0

        async def limited_receive() -> dict:
            nonlocal received
            message = await request._receive()
            if message.get("type") == "http.request":
                body = message.get("body") or b""
                received += len(body)
                if received > max_bytes:
                    return {"type": "http.request", "body": b"", "more_body": False}
            return message

        original_receive = request._receive
        request._receive = limited_receive  # type: ignore
        try:
            response = await call_next(request)
            if received > max_bytes:
                return Response(
                    content='{"error":"payload too large"}',
                    media_type="application/json",
                    status_code=413,
                )
            return response
        finally:
            request._receive = original_receive  # type: ignore


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response


class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, app: ASGIApp, connect_timeout: float, request_timeout: float
    ) -> None:
        super().__init__(app)
        self.connect_timeout = max(0.1, connect_timeout)
        self.request_timeout = max(0.1, request_timeout)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            # Allow dynamic override via env for tests
            timeout = float(os.getenv("REQUEST_TIMEOUT_SEC", str(self.request_timeout)))
            return await asyncio.wait_for(call_next(request), timeout=timeout)
        except asyncio.TimeoutError:
            req_id = getattr(request.state, "request_id", "")
            return Response(
                content=f'{{"error":"request timeout","request_id":"{req_id}"}}',
                media_type="application/json",
                status_code=504,
            )


class TokenBucketLimiter(BaseHTTPMiddleware):
    """Simple per-IP token bucket. Single-process only.

    Global bucket from RATE_LIMIT_GLOBAL_PER_MIN; optional override for /v1/chat.
    """

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        self.buckets: Dict[Tuple[str, str], Tuple[float, float]] = defaultdict(
            lambda: (time.time(), float(settings.RATE_LIMIT_GLOBAL_PER_MIN))
        )

    def _refill(self, key: Tuple[str, str], capacity_per_min: int) -> None:
        last, tokens = self.buckets[key]
        now = time.time()
        tokens = min(
            float(capacity_per_min), tokens + (now - last) * (capacity_per_min / 60.0)
        )
        self.buckets[key] = (now, tokens)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        # Allow well-known lightweight endpoints to bypass limiting
        if path in {"/health", "/healthz", "/metrics"}:
            return await call_next(request)
        # Allow dynamic override via env for tests
        rl_global = int(
            os.getenv(
                "RATE_LIMIT_GLOBAL_PER_MIN",
                str(self.settings.RATE_LIMIT_GLOBAL_PER_MIN),
            )
        )
        rl_chat = int(
            os.getenv(
                "RATE_LIMIT_CHAT_PER_MIN", str(self.settings.RATE_LIMIT_CHAT_PER_MIN)
            )
        )
        capacity = rl_chat if path.startswith("/v1/chat") else rl_global
        key = (ip, "chat" if path.startswith("/v1/chat") else "global")
        self._refill(key, capacity)
        last, tokens = self.buckets[key]
        if tokens < 1.0:
            retry_after = 1
            return Response(
                content='{"error":"rate limit exceeded"}',
                media_type="application/json",
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )
        self.buckets[key] = (last, tokens - 1.0)
        return await call_next(request)
