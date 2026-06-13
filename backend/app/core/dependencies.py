import logging
import uuid
from typing import Annotated, AsyncGenerator

from dataclasses import dataclass

from fastapi import Cookie, Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access_token
from app.auth.roles import Role, require_role
from app.core.exceptions import NotFoundError, UnauthorizedError
from app.models.api_key import ApiKey
from app.database.session import async_session_factory
from app.models.user import User

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
    tp_access_token: Annotated[str | None, Cookie(alias="tp_access_token")] = None,
) -> User:
    from app.repositories.user import UserRepository
    from app.core.security_headers import get_access_from_cookie

    raw_token: str | None = None
    if credentials is not None:
        raw_token = credentials.credentials
    elif tp_access_token:
        raw_token = tp_access_token
    else:
        raw_token = get_access_from_cookie(request)

    if raw_token is None:
        raise UnauthorizedError("Authentication required")

    payload = decode_access_token(raw_token)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Invalid token payload")

    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError) as exc:
        raise UnauthorizedError("Invalid token payload") from exc

    from app.core.auth_cache import get_cached_user, set_cached_user
    from app.core.timing import timed

    async with timed("auth.get_current_user", slow_ms=100):
        cached = get_cached_user(user_id)
        if cached is not None and cached.is_active:
            return cached

        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        set_cached_user(user)
        return user


@dataclass
class IngestContext:
    api_key: ApiKey
    workspace_id: uuid.UUID


async def get_ingest_context(
    db: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> IngestContext:
    from app.services.api_key_service import ApiKeyService

    raw_key = x_api_key
    if not raw_key and credentials and credentials.credentials.startswith("aoh_"):
        raw_key = credentials.credentials
    if not raw_key:
        raise UnauthorizedError("API key required. Set X-API-Key header.")

    service = ApiKeyService(db)
    try:
        api_key = await service.authenticate(raw_key)
    except NotFoundError:
        raise UnauthorizedError("Invalid API key") from None
    scopes = api_key.scopes or ["ingest"]
    if "ingest" not in scopes and "*" not in scopes:
        raise UnauthorizedError("API key missing ingest scope")
    return IngestContext(api_key=api_key, workspace_id=api_key.workspace_id)


DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
ViewerUser = Annotated[User, require_role(Role.VIEWER)]
DeveloperUser = Annotated[User, require_role(Role.DEVELOPER)]
AdminUser = Annotated[User, require_role(Role.ADMIN)]
IngestAuth = Annotated[IngestContext, Depends(get_ingest_context)]
