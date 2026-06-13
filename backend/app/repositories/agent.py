import uuid
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.repositories.base import BaseRepository


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class AgentRepository(BaseRepository[Agent]):
    def __init__(self, session: AsyncSession):
        super().__init__(Agent, session)

    async def search(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        owner: Optional[str] = None,
        search: Optional[str] = None,
        tags: Optional[list[str]] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Agent], int]:
        filters = []
        if workspace_id:
            filters.append(Agent.workspace_id == workspace_id)
        if status:
            filters.append(Agent.status == status)
        if owner:
            filters.append(Agent.owner == owner)
        if search:
            escaped = _escape_like(search[:200])
            filters.append(
                or_(
                    Agent.name.ilike(f"%{escaped}%", escape="\\"),
                    Agent.description.ilike(f"%{escaped}%", escape="\\"),
                )
            )
        if tags:
            filters.append(Agent.tags.contains(tags))

        where_clause = and_(*filters) if filters else True

        count_stmt = select(func.count()).select_from(Agent).where(where_clause)
        total = await self.count(count_stmt)

        data_stmt = (
            select(Agent)
            .where(where_clause)
            .offset(offset)
            .limit(limit)
            .order_by(Agent.created_at.desc())
        )
        items = await self.get_many(data_stmt)

        return items, total
