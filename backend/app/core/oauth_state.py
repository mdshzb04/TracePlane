"""Signed OAuth state tokens for CSRF protection."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

from app.core.config import settings

_STATE_TTL_SECONDS = 600


def create_oauth_state() -> str:
    payload = {
        "nonce": secrets.token_urlsafe(16),
        "exp": int(time.time()) + _STATE_TTL_SECONDS,
    }
    data = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
    sig = hmac.new(
        settings.SECRET_KEY.encode(),
        data.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{data}.{sig}"


def verify_oauth_state(state: str) -> bool:
    if not state or "." not in state:
        return False
    data, sig = state.rsplit(".", 1)
    expected = hmac.new(
        settings.SECRET_KEY.encode(),
        data.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return False
    try:
        payload = json.loads(base64.urlsafe_b64decode(data.encode()))
    except (json.JSONDecodeError, ValueError):
        return False
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return False
    return bool(payload.get("nonce"))
