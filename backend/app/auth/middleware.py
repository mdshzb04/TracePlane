import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

_SKIP_PATHS = {"/health", "/health/ready", "/docs", "/openapi.json", "/redoc"}


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        request_id = getattr(request.state, "request_id", "-")
        client_ip = request.client.host if request.client else "unknown"

        logger.info(
            "-> %s %s [request_id=%s ip=%s]",
            request.method,
            request.url.path,
            request_id,
            client_ip,
        )
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        log = logger.warning if duration_ms >= 1000 else logger.info
        log(
            "<- %s %s %d [request_id=%s duration_ms=%.1f]",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
            duration_ms,
        )
        return response
