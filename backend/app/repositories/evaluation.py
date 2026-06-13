import uuid
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation
from app.repositories.base import BaseRepository


class EvaluationRepository(BaseRepository[Evaluation]):
    def __init__(self, session: AsyncSession):
        super().__init__(Evaluation, session)

    async def search(
        self,
        *,
        agent_id: Optional[uuid.UUID] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Evaluation], int]:
        from sqlalchemy import func

        filters = []
        if agent_id:
            filters.append(Evaluation.agent_id == agent_id)
        if min_score is not None:
            filters.append(Evaluation.score >= min_score)
        if max_score is not None:
            filters.append(Evaluation.score <= max_score)

        where_clause = and_(*filters) if filters else True

        count_stmt = select(func.count()).select_from(Evaluation).where(where_clause)
        total = await self.count(count_stmt)

        data_stmt = (
            select(Evaluation)
            .where(where_clause)
            .offset(offset)
            .limit(limit)
            .order_by(Evaluation.evaluation_date.desc())
        )
        items = await self.get_many(data_stmt)
        return items, total