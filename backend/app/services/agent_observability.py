import uuid

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.workspace_scope import get_agent_in_workspace
from app.models.agent import Agent
from app.models.execution import Execution
from app.models.trace_span import TraceSpan
from app.repositories.agent import AgentRepository
from app.schemas.agent import AgentDetailRead, AgentHealthMetrics
from app.services.health_engine import compute_health


class AgentObservabilityService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.agent_repo = AgentRepository(session)

    async def get_agent_detail(self, agent_id: uuid.UUID, workspace_id: uuid.UUID) -> AgentDetailRead:
        agent = await get_agent_in_workspace(self.session, agent_id, workspace_id)
        health = await self._health_for_agent(agent_id)
        data = agent.to_dict()
        return AgentDetailRead(**data, health=health)

    async def get_agent_health(self, agent_id: uuid.UUID) -> AgentHealthMetrics:
        return await self._health_for_agent(agent_id)

    async def _health_for_agent(self, agent_id: uuid.UUID) -> AgentHealthMetrics:
        span_latency = (
            select(func.max(TraceSpan.latency_ms))
            .where(
                TraceSpan.execution_id == Execution.id,
                TraceSpan.latency_ms.isnot(None),
                TraceSpan.latency_ms > 0,
            )
            .correlate(Execution)
            .scalar_subquery()
        )
        effective_latency = func.coalesce(func.nullif(Execution.latency_ms, 0), span_latency)

        stmt = (
            select(
                func.count().label("total_executions"),
                func.avg(case((Execution.status == "success", 1), else_=0)).label("success_rate"),
                func.avg(case((Execution.status == "failed", 1), else_=0)).label("error_rate"),
                func.avg(effective_latency).label("avg_latency_ms"),
                func.sum(Execution.estimated_cost).label("total_cost"),
            )
            .where(Execution.agent_id == agent_id)
        )
        row = (await self.session.execute(stmt)).one()
        total = int(row.total_executions or 0)
        if total == 0:
            return AgentHealthMetrics(
                health_score=100.0,
                total_executions=0,
                success_rate=100.0,
                error_rate=0.0,
                avg_latency_ms=0.0,
                total_cost=0.0,
            )

        breakdown = compute_health(
            total_executions=total,
            success_rate_pct=float(row.success_rate or 0) * 100,
            error_rate_pct=float(row.error_rate or 0) * 100,
            avg_latency_ms=float(row.avg_latency_ms or 0),
            total_cost=float(row.total_cost or 0),
        )
        return AgentHealthMetrics(
            health_score=breakdown.health_score,
            total_executions=breakdown.total_executions,
            success_rate=breakdown.success_rate,
            error_rate=breakdown.error_rate,
            avg_latency_ms=breakdown.avg_latency_ms,
            total_cost=breakdown.total_cost,
        )
