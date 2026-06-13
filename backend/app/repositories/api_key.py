import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.repositories.base import BaseRepository


class ApiKeyRepository(BaseRepository[ApiKey]):
    def __init__(self, session: AsyncSession):
        super().__init__(ApiKey, session)

    async def get_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)  # noqa: E712
        return await self.get_one(stmt)

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[ApiKey]:
        stmt = (
            select(ApiKey)
            .where(ApiKey.workspace_id == workspace_id)
            .order_by(ApiKey.created_at.desc())
        )
        return await self.get_many(stmt)
