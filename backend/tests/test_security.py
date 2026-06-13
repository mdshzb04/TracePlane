from app.auth.jwt import create_access_token, create_refresh_token, decode_access_token, decode_refresh_token
from app.core.rate_limit import check_rate_limit
from app.core.security_headers import hash_refresh_token, new_csrf_token


def test_access_token_roundtrip():
    token = create_access_token("user-1", "developer")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-1"
    assert payload["role"] == "developer"


def test_refresh_token_rotation_metadata():
    token, jti, family_id = create_refresh_token("user-1")
    payload = decode_refresh_token(token)
    assert payload is not None
    assert payload["jti"] == jti
    assert payload["family_id"] == family_id


def test_refresh_token_family_preserved():
    token, jti, family = create_refresh_token("user-1", family_id="abc")
    assert family == "abc"
    assert jti


def test_refresh_token_hash_stable():
    assert hash_refresh_token("abc") == hash_refresh_token("abc")
    assert hash_refresh_token("abc") != hash_refresh_token("def")


def test_csrf_token_length():
    assert len(new_csrf_token()) >= 32


def test_rate_limit_allows_then_blocks():
    path = "/api/v1/auth/login"
    key = "ip:127.0.0.1"
    for _ in range(20):
        allowed, _ = check_rate_limit(key, path)
        assert allowed is True
    allowed, headers = check_rate_limit(key, path)
    assert allowed is False
    assert headers.get("X-RateLimit-Limit") == "20"
