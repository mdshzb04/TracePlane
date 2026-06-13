import uuid
from typing import Literal, Optional

from sqlalchemy import String, and_, case, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only
from sqlalchemy.types import Integer

from app.core.format import format_cost
from app.models.agent import Agent
from app.models.execution import Execution
from app.repositories.base import BaseRepository


class ExecutionRepository(BaseRepository[Execution]):
    def __init__(self, session: AsyncSession):
        super().__init__(Execution, session)

    def _token_total_expr(self):
        return func.coalesce(
            cast(Execution.token_usage["total_tokens"].astext, Integer),
            cast(Execution.token_usage["input_tokens"].astext, Integer)
            + cast(Execution.token_usage["output_tokens"].astext, Integer),
            0,
        )

    def _workspace_join(self, workspace_id: Optional[uuid.UUID]):
        if workspace_id:
            return Execution.__table__.join(Agent, Agent.id == Execution.agent_id)
        return Execution.__table__

    def _build_filters(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        search: Optional[str] = None,
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
        min_latency: Optional[int] = None,
        max_latency: Optional[int] = None,
        min_tokens: Optional[int] = None,
    ) -> list:
        filters = []
        if workspace_id:
            filters.append(Agent.workspace_id == workspace_id)
        if agent_id:
            filters.append(Execution.agent_id == agent_id)
        if status:
            filters.append(Execution.status == status)
        if model:
            filters.append(Execution.model.ilike(f"%{model}%"))
        if provider:
            filters.append(Agent.provider.ilike(f"%{provider}%"))
        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    Execution.model.ilike(term),
                    Agent.name.ilike(term),
                    Agent.provider.ilike(term),
                    cast(Execution.id, String).ilike(term),
                )
            )
        if min_cost is not None:
            filters.append(Execution.estimated_cost >= min_cost)
        if max_cost is not None:
            filters.append(Execution.estimated_cost <= max_cost)
        if min_latency is not None:
            filters.append(Execution.latency_ms >= min_latency)
        if max_latency is not None:
            filters.append(Execution.latency_ms <= max_latency)
        if min_tokens is not None:
            filters.append(self._token_total_expr() >= min_tokens)
        return filters

    async def search(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "started_at",
        sort_order: str = "desc",
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
        min_latency: Optional[int] = None,
        max_latency: Optional[int] = None,
        min_tokens: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[tuple[Execution, Optional[str], Optional[str]]], int]:
        filters = self._build_filters(
            workspace_id=workspace_id,
            agent_id=agent_id,
            status=status,
            model=model,
            provider=provider,
            search=search,
            min_cost=min_cost,
            max_cost=max_cost,
            min_latency=min_latency,
            max_latency=max_latency,
            min_tokens=min_tokens,
        )
        where_clause = and_(*filters) if filters else True

        from_clause = self._workspace_join(workspace_id)
        count_stmt = select(func.count()).select_from(from_clause).where(where_clause)
        total = await self.count(count_stmt)

        sort_columns = {
            "started_at": Execution.started_at,
            "latency_ms": Execution.latency_ms,
            "estimated_cost": Execution.estimated_cost,
            "total_tokens": self._token_total_expr(),
        }
        sort_col = sort_columns.get(sort_by, Execution.started_at)
        order = sort_col.desc() if sort_order == "desc" else sort_col.asc()

        data_stmt = (
            select(Execution, Agent.name, Agent.provider)
            .options(
                load_only(
                    Execution.id,
                    Execution.agent_id,
                    Execution.status,
                    Execution.latency_ms,
                    Execution.token_usage,
                    Execution.estimated_cost,
                    Execution.model,
                    Execution.replay_of_id,
                    Execution.is_replay,
                    Execution.started_at,
                    Execution.completed_at,
                    Execution.created_at,
                    Execution.updated_at,
                )
            )
            .select_from(from_clause)
            .where(where_clause)
            .order_by(order.nullslast())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(data_stmt)
        items = [(row[0], row[1], row[2]) for row in result.all()]
        return items, total

    async def summary(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        search: Optional[str] = None,
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
        min_latency: Optional[int] = None,
        max_latency: Optional[int] = None,
        min_tokens: Optional[int] = None,
    ) -> dict:
        filters = self._build_filters(
            workspace_id=workspace_id,
            agent_id=agent_id,
            status=status,
            model=model,
            provider=provider,
            search=search,
            min_cost=min_cost,
            max_cost=max_cost,
            min_latency=min_latency,
            max_latency=max_latency,
            min_tokens=min_tokens,
        )

        where_clause = and_(*filters) if filters else True
        token_expr = self._token_total_expr()
        from_clause = self._workspace_join(workspace_id)

        stmt = (
            select(
                func.count().label("total_executions"),
                func.coalesce(func.sum(Execution.estimated_cost), 0).label("total_cost"),
                func.coalesce(func.sum(token_expr), 0).label("total_tokens"),
                func.coalesce(func.avg(Execution.latency_ms), 0).label("avg_latency_ms"),
                func.coalesce(func.sum(case((Execution.status == "success", 1), else_=0)), 0).label("success_count"),
                func.coalesce(func.sum(case((Execution.status == "failed", 1), else_=0)), 0).label("failed_count"),
            )
            .select_from(from_clause)
            .where(where_clause)
        )

        row = (await self.session.execute(stmt)).one()
        return {
            "total_executions": int(row.total_executions or 0),
            "total_cost": format_cost(float(row.total_cost or 0)) or 0.0,
            "total_tokens": int(row.total_tokens or 0),
            "avg_latency_ms": round(float(row.avg_latency_ms or 0), 2),
            "success_count": int(row.success_count or 0),
            "failed_count": int(row.failed_count or 0),
        }
