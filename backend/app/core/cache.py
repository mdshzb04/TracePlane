"""Simple in-process TTL cache for hot read endpoints."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Callable

_store: dict[str, tuple[float, Any]] = {}


def cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    raw = json.dumps({"a": args, "k": kwargs}, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"{prefix}:{digest}"


def get_cached(key: str) -> Any | None:
    entry = _store.get(key)
    if entry is None:
        return None
    expires_at, value = entry
    if time.time() > expires_at:
        _store.pop(key, None)
        return None
    return value


def set_cached(key: str, value: Any, ttl_seconds: int = 30) -> None:
    _store[key] = (time.time() + ttl_seconds, value)


async def cached_async(
    key: str,
    ttl_seconds: int,
    factory: Callable[[], Any],
) -> Any:
    hit = get_cached(key)
    if hit is not None:
        return hit
    value = await factory()
    set_cached(key, value, ttl_seconds)
    return value


def delete_cached(key: str) -> None:
    _store.pop(key, None)


def clear_cache(prefix: str | None = None) -> None:
    if prefix is None:
        _store.clear()
        return
    for key in list(_store):
        if key.startswith(f"{prefix}:"):
            _store.pop(key, None)
