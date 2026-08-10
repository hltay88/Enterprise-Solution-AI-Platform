"""Simple in-process rate limit middleware (Sprint 5.5 hardening)."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        limit = int(getattr(settings, "atlas_rate_limit_per_minute", 0) or 0)
        if limit <= 0:
            return await call_next(request)

        # Skip health checks
        if request.url.path.endswith("/health"):
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        key = f"{client}:{request.url.path}"
        now = time.time()
        window = self._hits[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {"code": "rate_limited", "message": "Too many requests"},
                },
            )
        window.append(now)
        return await call_next(request)
