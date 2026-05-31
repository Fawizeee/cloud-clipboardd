"""
Request / Response Logging Middleware
======================================
Logs every HTTP request and its response status + duration using Python's
standard logging library. Uses a unique request-ID header for tracing.
"""

import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("cloud_clipboard")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Attach the request ID so routes can read it from request.state
        request.state.request_id = request_id

        response: Response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "%s %s %s %.1fms [%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )

        # Expose the request ID in the response so clients can correlate logs
        response.headers["X-Request-ID"] = request_id
        return response
