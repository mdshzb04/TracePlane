import asyncio

from app.core.cache import cache_key, cached_async, clear_cache, get_cached, set_cached


def test_cache_key_stable():
    assert cache_key("p", 1, foo="bar") == cache_key("p", 1, foo="bar")


def test_cache_ttl_expiry(monkeypatch):
    clear_cache()
    set_cached("k", "v", ttl_seconds=10)
    assert get_cached("k") == "v"
    monkeypatch.setattr("app.core.cache.time.time", lambda: 9999999999)
    assert get_cached("k") is None


def test_cached_async():
    clear_cache()
    calls = {"n": 0}

    async def factory():
        calls["n"] += 1
        return {"ok": True}

    async def run():
        first = await cached_async("async:k", 30, factory)
        second = await cached_async("async:k", 30, factory)
        return first, second

    first, second = asyncio.run(run())
    assert first == second == {"ok": True}
    assert calls["n"] == 1
