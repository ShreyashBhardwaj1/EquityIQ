"""
FastAPI Middleware for structured logging of HTTP requests.
"""

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("equityiq.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP middleware logging request info, status codes, and execution duration.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Intercepts and processes the request.

        Args:
            request: The incoming request.
            call_next: The endpoint processing function.

        Returns:
            The HTTP response.
        """
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path
        client = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            logger.info(
                f"HTTP {method} {path} - {response.status_code}",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "latency_ms": round(duration_ms, 2),
                    "client": client,
                },
            )
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                f"HTTP {method} {path} - Failed: {exc}",
                exc_info=True,
                extra={
                    "method": method,
                    "path": path,
                    "latency_ms": round(duration_ms, 2),
                    "client": client,
                },
            )
            raise exc
