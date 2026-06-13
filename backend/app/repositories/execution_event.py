import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_event import ExecutionEvent
from app.repositories.base import BaseRepository


class ExecutionEventRepository(BaseRepository[ExecutionEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(ExecutionEvent, session)

    async def get_by_execution_id(
        self, execution_id: uuid.UUID, offset: int = 0, limit: int = 100
    ) -> list[ExecutionEvent]:
        stmt = (
            select(ExecutionEvent)
            .where(ExecutionEvent.execution_id == execution_id)
            .offset(offset)
            .limit(limit)
            .order_by(ExecutionEvent.timestamp.asc())
        )
        return await self.get_many(stmt)