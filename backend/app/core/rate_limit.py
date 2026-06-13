"""Redis-backed sliding-window rate limiter with in-memory fallback."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from threading import Lock

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

_lock = Lock()
_buckets: dict[str, list[float]] = defaultdict(list)
_backend_used: str = "memory"
_last_redis_error: str | None = None

# (max_requests, window_seconds) — longest prefix match wins
LIMITS: dict[str, tuple[int, int]] = {
    "/api/v1/auth/login": (20, 60),
    "/api/v1/auth/register": (10, 60),
    "/api/v1/auth/refresh": (30, 60),
    "/api/v1/auth/github": (20, 60),
    "/api/v1/auth/set-password": (10, 60),
    "/api/v1/api-keys": (60, 60),
    "/api/v1/ingest": (300, 60),
}


def _client_key(request: Request) -> str:
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        return f"key:{api_key[:16]}"
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return f"jwt:{auth[7:23]}"
    forwarded = request.headers.get("X-Forwarded-For")
    ip = (
        forwarded.split(",")[0].strip()
        if forwarded
        else (request.client.host if request.client else "unknown")
    )
    return f"ip:{ip}"


def _limit_for_path(path: str) -> tuple[int, int] | None:
    best: tuple[int, int] | None = None
    best_len = -1
    for prefix, limit in LIMITS.items():
        if path.startswith(prefix) and len(prefix) > best_len:
            best = limit
            best_len = len(prefix)
    return best


def _memory_check(bucket_key: str, max_req: int, window: int) -> tuple[bool, int]:
    now = time.time()
    with _lock:
        hits = _buckets[bucket_key]
        hits[:] = [t for t in hits if now - t < window]
        remaining = max(0, max_req - len(hits))
        if len(hits) >= max_req:
            return False, 0
        hits.append(now)
        return True, remaining - 1


def _redis_check(bucket_key: str, max_req: int, window: int) -> tuple[bool, int] | None:
    global _last_redis_error
    client = get_redis()
    if client is None:
        return None
    try:
        now = time.time()
        window_start = now - window
        redis_key = f"traceplane:rl:{bucket_key}"
        pipe = client.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zcard(redis_key)
        _, count = pipe.execute()
        if count >= max_req:
            return False, 0
        member = f"{now}:{uuid.uuid4().hex[:8]}"
        pipe = client.pipeline()
        pipe.zadd(redis_key, {member: now})
        pipe.expire(redis_key, window + 1)
        pipe.zcard(redis_key)
        pipe.execute()
        remaining = max(0, max_req - count - 1)
        _last_redis_error = None
        return True, remaining
    except Exception as exc:
        _last_redis_error = str(exc)
        logger.warning("Redis rate limit failed, using memory fallback: %s", exc)
        return None


def check_rate_limit(key: str, path: str) -> tuple[bool, dict[str, str]]:
    """Return (allowed, headers) for rate limit metadata."""
    global _backend_used
    spec = _limit_for_path(path)
    if spec is None:
        return True, {}
    max_req, window = spec
    bucket_key = f"{key}:{path}"

    redis_result = _redis_check(bucket_key, max_req, window)
    if redis_result is not None:
        _backend_used = "redis"
        allowed, remaining = redis_result
    else:
        _backend_used = "memory"
        allowed, remaining = _memory_check(bucket_key, max_req, window)

    headers = {
        "X-RateLimit-Limit": str(max_req),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Backend": _backend_used,
    }
    return allowed, headers


def get_rate_limit_status() -> dict:
    """Monitoring snapshot for readiness endpoints."""
    return {
        "backend": _backend_used,
        "redis_configured": bool(settings.REDIS_URL),
        "redis_available": get_redis() is not None,
        "last_redis_error": _last_redis_error,
        "protected_prefixes": list(LIMITS.keys()),
    }


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if settings.ENV == "test":
            return await call_next(request)
        path = request.url.path
        allowed, headers = check_rate_limit(_client_key(request), path)
        if not allowed:
            logger.info("Rate limit exceeded: %s %s", request.method, path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Retry later."},
                headers={**headers, "Retry-After": "60"},
            )
        response = await call_next(request)
        for k, v in headers.items():
            response.headers[k] = v
        return response
