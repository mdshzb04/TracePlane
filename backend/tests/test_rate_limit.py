from unittest.mock import MagicMock, patch

from app.core.rate_limit import (
    LIMITS,
    _limit_for_path,
    _memory_check,
    check_rate_limit,
    get_rate_limit_status,
)


def test_limit_for_longest_prefix():
    assert _limit_for_path("/api/v1/ingest/trace") == LIMITS["/api/v1/ingest"]
    assert _limit_for_path("/api/v1/agents") is None


def test_memory_fallback_blocks():
    key = "test:memory:block"
    for _ in range(5):
        allowed, _ = _memory_check(key, 5, 60)
        assert allowed
    allowed, _ = _memory_check(key, 5, 60)
    assert not allowed


def test_check_rate_limit_uses_memory_when_redis_unavailable():
    with patch("app.core.rate_limit._redis_check", return_value=None):
        allowed, headers = check_rate_limit("ip:1.2.3.4", "/api/v1/auth/login")
        assert allowed
        assert headers["X-RateLimit-Backend"] == "memory"


def test_check_rate_limit_redis_path():
    with patch("app.core.rate_limit._redis_check", return_value=(True, 59)):
        allowed, headers = check_rate_limit("ip:1.2.3.4", "/api/v1/auth/login")
        assert allowed
        assert headers["X-RateLimit-Backend"] == "redis"
        assert headers["X-RateLimit-Remaining"] == "59"


def test_rate_limit_status_snapshot():
    status = get_rate_limit_status()
    assert "backend" in status
    assert "/api/v1/ingest" in status["protected_prefixes"]
