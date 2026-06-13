"""In-process cache for authenticated user lookups."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.cache import clear_cache, delete_cached, get_cached, set_cached
from app.models.user import User

_USER_TTL = 60


def _user_cache_key(user_id: uuid.UUID) -> str:
    return f"auth_user:{user_id}"


def _serialize_user(user: User) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "workspace_id": str(user.workspace_id) if user.workspace_id else None,
        "is_active": user.is_active,
        "provider": user.provider,
        "github_id": user.github_id,
        "avatar_url": user.avatar_url,
        "password_hash": user.password_hash,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def _deserialize_user(data: dict[str, Any]) -> User:
    from datetime import datetime

    user = User(
        id=uuid.UUID(data["id"]),
        email=data["email"],
        full_name=data.get("full_name"),
        role=data.get("role", "viewer"),
        workspace_id=uuid.UUID(data["workspace_id"]) if data.get("workspace_id") else None,
        is_active=bool(data.get("is_active", True)),
        provider=data.get("provider"),
        github_id=data.get("github_id"),
        avatar_url=data.get("avatar_url"),
        password_hash=data.get("password_hash"),
    )
    if data.get("created_at"):
        user.created_at = datetime.fromisoformat(data["created_at"])
    if data.get("updated_at"):
        user.updated_at = datetime.fromisoformat(data["updated_at"])
    return user


def get_cached_user(user_id: uuid.UUID) -> User | None:
    raw = get_cached(_user_cache_key(user_id))
    if raw is None:
        return None
    return _deserialize_user(raw)


def set_cached_user(user: User) -> None:
    set_cached(_user_cache_key(user.id), _serialize_user(user), _USER_TTL)


def invalidate_user_cache(user_id: uuid.UUID | None = None) -> None:
    if user_id is None:
        clear_cache("auth_user")
        return
    delete_cached(_user_cache_key(user_id))
