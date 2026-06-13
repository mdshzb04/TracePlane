import uuid

from app.auth.jwt import create_access_token
from app.core.events import channel_for_workspace
from app.core.ws_auth import extract_ws_token


class _FakeWebSocket:
    def __init__(self, *, token: str | None = None, cookie: str | None = None):
        self.query_params = {"token": token} if token else {}
        self.cookies = {"tp_access_token": cookie} if cookie else {}


def test_extract_ws_token_from_query():
    ws = _FakeWebSocket(token="abc123")
    assert extract_ws_token(ws) == "abc123"


def test_extract_ws_token_from_cookie():
    ws = _FakeWebSocket(cookie="cookie-token")
    assert extract_ws_token(ws) == "cookie-token"


def test_extract_ws_token_query_over_cookie():
    ws = _FakeWebSocket(token="query", cookie="cookie")
    assert extract_ws_token(ws) == "query"


def test_extract_ws_token_missing():
    ws = _FakeWebSocket()
    assert extract_ws_token(ws) is None


def test_workspace_channel_isolation():
    ws_a = channel_for_workspace(uuid.UUID("00000000-0000-0000-0000-000000000001"))
    ws_b = channel_for_workspace(uuid.UUID("00000000-0000-0000-0000-000000000002"))
    assert ws_a != ws_b
    assert ws_a.startswith("agentops:live:")


def test_valid_access_token_decodes():
    token = create_access_token(str(uuid.uuid4()), "developer")
    from app.auth.jwt import decode_access_token

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["type"] == "access"
