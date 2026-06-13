"""Self-observability — structured request tracing for Traceplane backend."""

from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("traceplane.trace")

_trace_id: ContextVar[str] = ContextVar("trace_id", default="")


def current_trace_id() -> str:
    return _trace_id.get() or ""


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        _trace_id.set(trace_id)
        start = time.perf_counter()
        response = None
        error: str | None = None
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            error = str(exc)
            raise
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            status = response.status_code if response else 500
            logger.info(
                "http.request",
                extra={
                    "trace_id": trace_id,
                    "span": "http.request",
                    "method": request.method,
                    "path": request.url.path,
                    "status": status,
                    "duration_ms": duration_ms,
                    "error": error,
                },
            )
            if response:
                response.headers["X-Trace-ID"] = trace_id
