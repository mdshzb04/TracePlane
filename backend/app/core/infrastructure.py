"""Redis and Celery connectivity checks with graceful degradation."""

import logging
import ssl
from typing import Any
from urllib.parse import urlparse

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


def _redis_ssl_kwargs(url: str) -> dict[str, Any]:
    if url.startswith("rediss://"):
        return {"ssl_cert_reqs": ssl.CERT_NONE}
    return {}


def get_redis() -> redis.Redis | None:
    """Return a Redis client or None if Redis is unavailable (non-fatal)."""
    global _redis_client
    if not settings.REDIS_URL:
        return None

    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except Exception:
            logger.warning("Redis connection lost, reconnecting")
            _redis_client = None

    try:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            **_redis_ssl_kwargs(settings.REDIS_URL),
        )
        _redis_client.ping()
        logger.info("Redis connected")
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable: %s", exc)
        _redis_client = None
        return None


def check_redis() -> dict[str, Any]:
    if not settings.REDIS_URL:
        return {"configured": False, "status": "skipped", "detail": "REDIS_URL not set"}
    client = get_redis()
    if client is None:
        return {"configured": True, "status": "error", "detail": "connection failed"}
    try:
        client.ping()
        return {"configured": True, "status": "ok"}
    except Exception as exc:
        return {"configured": True, "status": "error", "detail": str(exc)}


def check_celery_broker() -> dict[str, Any]:
    broker = settings.CELERY_BROKER_URL or settings.REDIS_URL
    if not broker:
        return {"configured": False, "status": "skipped", "detail": "CELERY_BROKER_URL not set"}
    try:
        client = redis.from_url(broker, decode_responses=True, **_redis_ssl_kwargs(broker))
        client.ping()
        return {"configured": True, "status": "ok", "broker": urlparse(broker).hostname}
    except Exception as exc:
        return {"configured": True, "status": "error", "detail": str(exc)}


def celery_worker_reachable() -> bool:
    if not settings.CELERY_ENABLED:
        return False
    try:
        from app.celery_app import celery_app

        inspect = celery_app.control.inspect(timeout=2.0)
        ping = inspect.ping()
        return bool(ping)
    except Exception as exc:
        logger.debug("Celery worker inspect failed: %s", exc)
        return False
