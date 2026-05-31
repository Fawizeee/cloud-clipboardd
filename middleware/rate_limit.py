"""
In-Memory Rate Limiting Middleware
====================================
Provides a simple sliding-window rate limiter for auth-related endpoints.
Uses an in-memory store (TTLCache via cachetools) — suitable for a single
process. Replace with a Redis-backed solution for multi-instance deployments.

Default: 10 requests per minute per IP on paths starting with /api/v1/auth
"""

import time
from collections import defaultdict, deque

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter.

    Attributes
    ----------
    rate_limit_paths : tuple of path prefixes that should be rate-limited
    rpm             : maximum requests per minute per IP
    """

    rate_limit_paths = ("/api/v1/auth",)

    def __init__(self, app, rpm: int | None = None):
        super().__init__(app)
        self.rpm = rpm or settings.RATE_LIMIT_AUTH_RPM
        # ip -> deque of timestamps (epoch seconds)
        self._windows: dict[str, deque] = defaultdict(deque)

    def _is_rate_limited_path(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.rate_limit_paths)

    def _check_rate_limit(self, ip: str) -> bool:
        """Return True if the request should be blocked."""
        now = time.time()
        window = self._windows[ip]

        # Evict timestamps older than 60 seconds
        while window and window[0] < now - 60:
            window.popleft()

        if len(window) >= self.rpm:
            return True

        window.append(now)
        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        if self._is_rate_limited_path(request.url.path):
            client_ip = request.client.host if request.client else "unknown"
            if self._check_rate_limit(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": {
                            "message": "Too many requests. Please wait before retrying.",
                            "code": "RATE_LIMITED",
                        },
                    },
                    headers={"Retry-After": "60"},
                )
        return await call_next(request)
