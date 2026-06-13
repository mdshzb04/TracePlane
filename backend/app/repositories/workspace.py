import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    def __init__(self, session: AsyncSession):
        super().__init__(Workspace, session)

    async def get_by_slug(self, slug: str) -> Optional[Workspace]:
        stmt = select(Workspace).where(Workspace.slug == slug)
        return await self.get_one(stmt)

    async def get_or_create_for_user(self, user_id: uuid.UUID, name: str, slug: str) -> Workspace:
        existing = await self.get_by_slug(slug)
        if existing:
            return existing
        workspace = Workspace(name=name, slug=slug)
        workspace = await self.create(workspace)
        await self.session.flush()
        return workspace
