"""WebSocket authentication and workspace scoping."""

from __future__ import annotations

import logging
import uuid

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access_token
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.api_key_service import ApiKeyService

logger = logging.getLogger(__name__)


def extract_ws_token(websocket: WebSocket) -> str | None:
    """Read JWT from query param or httpOnly session cookie."""
    token = websocket.query_params.get("token")
    if token:
        return token
    return websocket.cookies.get("tp_access_token")


async def authenticate_websocket(websocket: WebSocket, db: AsyncSession) -> tuple[User, uuid.UUID] | None:
    """Validate JWT and resolve the user's workspace. Returns None if unauthorized."""
    raw = extract_ws_token(websocket)
    if not raw:
        logger.debug("WS auth failed: no token")
        return None

    payload = decode_access_token(raw)
    if payload is None:
        logger.debug("WS auth failed: invalid token")
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        return None

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        logger.debug("WS auth failed: user inactive or missing")
        return None

    workspace_id = await ApiKeyService(db).ensure_user_workspace(user)
    return user, workspace_id
