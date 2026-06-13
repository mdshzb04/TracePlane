import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key import generate_api_key, hash_api_key
from app.core.exceptions import NotFoundError
from app.models.api_key import ApiKey
from app.models.user import User
from app.repositories.api_key import ApiKeyRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyRead

logger = logging.getLogger(__name__)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "workspace"


class ApiKeyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ApiKeyRepository(session)
        self.workspace_repo = WorkspaceRepository(session)
        self.user_repo = UserRepository(session)

    async def ensure_user_workspace(self, user: User) -> uuid.UUID:
        if user.workspace_id:
            return user.workspace_id
        slug = _slugify(user.email.split("@")[0])
        workspace = await self.workspace_repo.get_or_create_for_user(
            user.id, name=f"{user.full_name or user.email}'s workspace", slug=slug
        )
        user.workspace_id = workspace.id
        await self.session.flush()
        return workspace.id

    async def create_key(self, user: User, data: ApiKeyCreate) -> ApiKeyCreateResponse:
        workspace_id = await self.ensure_user_workspace(user)
        full_key, key_hash, key_prefix = generate_api_key()
        api_key = ApiKey(
            workspace_id=workspace_id,
            name=data.name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            environment="default",
            scopes=["ingest"],
            created_by=user.id,
            is_active=True,
        )
        api_key = await self.repo.create(api_key)
        await self.session.flush()
        logger.info("API key created: %s for workspace %s", api_key.id, workspace_id)
        read = ApiKeyRead.model_validate(api_key)
        return ApiKeyCreateResponse(**read.model_dump(), key=full_key)

    async def list_keys(self, user: User) -> list[ApiKeyRead]:
        workspace_id = await self.ensure_user_workspace(user)
        keys = await self.repo.list_by_workspace(workspace_id)
        return [ApiKeyRead.model_validate(k) for k in keys]

    async def revoke_key(self, user: User, key_id: uuid.UUID) -> None:
        workspace_id = await self.ensure_user_workspace(user)
        key = await self.repo.get_by_id(key_id)
        if key is None or key.workspace_id != workspace_id:
            raise NotFoundError("ApiKey", str(key_id))
        await self.repo.update(key, {"is_active": False})

    async def authenticate(self, raw_key: str) -> ApiKey:
        key_hash = hash_api_key(raw_key)
        api_key = await self.repo.get_by_hash(key_hash)
        if api_key is None:
            raise NotFoundError("ApiKey", "invalid")
        if not api_key.is_active:
            raise NotFoundError("ApiKey", "revoked")
        return api_key

    async def record_usage(self, api_key: ApiKey, cost: float = 0.0) -> None:
        await self.repo.update(
            api_key,
            {
                "last_used_at": datetime.now(timezone.utc),
                "request_count": int(api_key.request_count or 0) + 1,
                "total_cost": float(api_key.total_cost or 0) + float(cost or 0),
            },
        )

    async def rotate_key(self, user: User, key_id: uuid.UUID) -> ApiKeyCreateResponse:
        workspace_id = await self.ensure_user_workspace(user)
        key = await self.repo.get_by_id(key_id)
        if key is None or key.workspace_id != workspace_id:
            raise NotFoundError("ApiKey", str(key_id))
        name = key.name
        await self.repo.update(key, {"is_active": False})
        return await self.create_key(user, ApiKeyCreate(name=f"{name} (rotated)"))
