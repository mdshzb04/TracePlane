import uuid
from datetime import datetime
from typing import Literal, Optional

from sqlalchemy import Integer, and_, case, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from app.core.time_buckets import bucket_label, resolve_bucket, zero_fill_series
from app.models.agent import Agent
from app.models.evaluation import Evaluation
from app.models.execution import Execution
from app.models.execution_event import ExecutionEvent
from app.models.workspace import Workspace
from app.services.health_engine import compute_health


def _token_total_expr():
    total = cast(Execution.token_usage["total_tokens"].astext, Integer)
    input_tokens = cast(Execution.token_usage["input_tokens"].astext, Integer)
    output_tokens = cast(Execution.token_usage["output_tokens"].astext, Integer)
    return func.coalesce(total, func.coalesce(input_tokens, 0) + func.coalesce(output_tokens, 0), 0)


def _input_tokens_expr():
    return cast(Execution.token_usage["input_tokens"].astext, Integer)


def _output_tokens_expr():
    return cast(Execution.token_usage["output_tokens"].astext, Integer)


def _cached_tokens_expr():
    return cast(Execution.token_usage["cached_tokens"].astext, Integer)


class AnalyticsRepository:
    """Data access layer for observability analytics aggregations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _execution_filters(
        self,
        *,
        agent_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        model: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> list:
        filters = []
        if agent_id:
            filters.append(Execution.agent_id == agent_id)
        if workspace_id:
            filters.append(Agent.workspace_id == workspace_id)
        if model:
            filters.append(Execution.model == model)
        if status:
            filters.append(Execution.status == status)
        if start_date:
            filters.append(Execution.started_at >= start_date)
        if end_date:
            filters.append(Execution.started_at <= end_date)
        if search:
            pattern = f"%{search}%"
            filters.append(
                (Execution.input.ilike(pattern))
                | (Execution.output.ilike(pattern))
                | (Execution.model.ilike(pattern))
            )
        return filters

    def _where(self, filters: list):
        return and_(*filters) if filters else True

    async def count_agents(self, workspace_id: Optional[uuid.UUID] = None) -> int:
        stmt = select(func.count()).select_from(Agent)
        if workspace_id:
            stmt = stmt.where(Agent.workspace_id == workspace_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    def _needs_agent_join(self, filters: list) -> bool:
        return any(
            getattr(f, "left", None) is Agent.workspace_id or str(f).startswith("agents.workspace_id")
            for f in filters
        )

    def _execution_from(self, filters: list):
        where = self._where(filters)
        if self._needs_agent_join(filters):
            return Execution, Execution.__table__.join(Agent, Agent.id == Execution.agent_id), where
        return Execution, Execution.__table__, where

    def _execution_base(self, filters: list):
        where = self._where(filters)
        if self._needs_agent_join(filters):
            return select(Execution).join(Agent, Agent.id == Execution.agent_id).where(where)
        return select(Execution).where(where)

    async def execution_stats(
        self,
        *,
        agent_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        join_agent = workspace_id is not None

        stmt = select(
            func.count().label("total"),
            func.count().filter(Execution.status == "success").label("success"),
            func.count().filter(Execution.status == "failed").label("failed"),
            func.avg(Execution.latency_ms).label("avg_latency_ms"),
            func.sum(_token_total_expr()).label("total_tokens"),
            func.coalesce(func.sum(_input_tokens_expr()), 0).label("input_tokens"),
            func.coalesce(func.sum(_output_tokens_expr()), 0).label("output_tokens"),
            func.coalesce(func.sum(Execution.estimated_cost), 0).label("total_cost"),
        )
        if join_agent:
            stmt = stmt.select_from(Execution).join(Agent, Agent.id == Execution.agent_id)
        else:
            stmt = stmt.select_from(Execution)
        row = (await self.session.execute(stmt.where(where))).one()

        return {
            "total": int(row.total or 0),
            "success": int(row.success or 0),
            "failed": int(row.failed or 0),
            "avg_latency_ms": float(row.avg_latency_ms or 0),
            "total_tokens": int(row.total_tokens or 0),
            "input_tokens": int(row.input_tokens or 0),
            "output_tokens": int(row.output_tokens or 0),
            "total_cost": float(row.total_cost or 0),
        }

    async def provider_outage_count(
        self,
        *,
        workspace_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count distinct providers with failed executions in the window."""
        filters = self._execution_filters(
            workspace_id=workspace_id,
            status="failed",
            start_date=start_date,
            end_date=end_date,
        )
        where = self._where(filters)
        stmt = (
            select(func.count(func.distinct(Agent.provider)))
            .select_from(Execution)
            .join(Agent, Agent.id == Execution.agent_id)
            .where(where, Agent.provider.isnot(None))
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def daily_time_series(
        self,
        metric: str,
        *,
        agent_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[tuple[str, float]]:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)

        if metric == "latency":
            value_expr = func.avg(Execution.latency_ms)
        elif metric == "cost":
            value_expr = func.sum(Execution.estimated_cost)
        elif metric == "tokens":
            value_expr = func.sum(_token_total_expr())
        else:
            raise ValueError(f"Unknown metric: {metric}")

        stmt = select(
            func.date_trunc("day", Execution.started_at).label("date"),
            value_expr.label("value"),
        )
        if workspace_id:
            stmt = stmt.select_from(Execution).join(Agent, Agent.id == Execution.agent_id)
        else:
            stmt = stmt.select_from(Execution)
        stmt = stmt.where(where).group_by(text("date")).order_by(text("date"))
        result = await self.session.execute(stmt)
        return [(str(row.date), float(row.value or 0)) for row in result]

    async def cost_by_agent(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
    ) -> list[dict]:
        filters = self._execution_filters(
            workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)

        stmt = (
            select(
                Execution.agent_id,
                Agent.name.label("agent_name"),
                func.sum(Execution.estimated_cost).label("total_cost"),
                func.count().label("execution_count"),
            )
            .join(Agent, Agent.id == Execution.agent_id)
            .where(where)
            .group_by(Execution.agent_id, Agent.name)
            .order_by(text("total_cost DESC"))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [
            {
                "agent_id": str(row.agent_id),
                "agent_name": row.agent_name,
                "total_cost": float(row.total_cost or 0),
                "execution_count": row.execution_count,
            }
            for row in result
        ]

    async def cost_by_model(
        self,
        *,
        agent_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict]:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)

        stmt = select(
            Execution.model,
            func.sum(Execution.estimated_cost).label("total_cost"),
            func.count().label("execution_count"),
            func.sum(_token_total_expr()).label("total_tokens"),
        )
        if workspace_id:
            stmt = stmt.select_from(Execution).join(Agent, Agent.id == Execution.agent_id)
        else:
            stmt = stmt.select_from(Execution)
        stmt = (
            stmt.where(where, Execution.model.isnot(None))
            .group_by(Execution.model)
            .order_by(text("total_cost DESC"))
        )
        result = await self.session.execute(stmt)
        return [
            {
                "model": row.model or "unknown",
                "total_cost": float(row.total_cost or 0),
                "execution_count": row.execution_count,
                "total_tokens": int(row.total_tokens or 0),
            }
            for row in result
        ]

    async def token_breakdown(
        self,
        *,
        agent_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        _, from_clause, _ = self._execution_from(filters)

        totals_row = (
            await self.session.execute(
                select(
                    func.sum(func.coalesce(_input_tokens_expr(), 0)).label("input_tokens"),
                    func.sum(func.coalesce(_output_tokens_expr(), 0)).label("output_tokens"),
                )
                .select_from(from_clause)
                .where(where)
            )
        ).one()
        input_total = int(totals_row.input_tokens or 0)
        output_total = int(totals_row.output_tokens or 0)

        by_model_stmt = (
            select(
                Execution.model,
                func.sum(_input_tokens_expr()).label("input_tokens"),
                func.sum(_output_tokens_expr()).label("output_tokens"),
                func.sum(_token_total_expr()).label("total_tokens"),
            )
            .select_from(from_clause)
            .where(where, Execution.model.isnot(None))
            .group_by(Execution.model)
        )
        by_model_result = await self.session.execute(by_model_stmt)
        by_model = [
            {
                "model": row.model or "unknown",
                "input_tokens": int(row.input_tokens or 0),
                "output_tokens": int(row.output_tokens or 0),
                "total_tokens": int(row.total_tokens or 0),
            }
            for row in by_model_result
        ]

        by_agent_stmt = (
            select(
                Execution.agent_id,
                Agent.name.label("agent_name"),
                func.sum(_token_total_expr()).label("total_tokens"),
            )
            .select_from(Execution)
            .join(Agent, Agent.id == Execution.agent_id)
            .where(where)
            .group_by(Execution.agent_id, Agent.name)
            .order_by(text("total_tokens DESC"))
            .limit(20)
        )
        by_agent_result = await self.session.execute(by_agent_stmt)
        by_agent = [
            {
                "agent_id": str(row.agent_id),
                "agent_name": row.agent_name,
                "total_tokens": int(row.total_tokens or 0),
            }
            for row in by_agent_result
        ]

        return {
            "input_tokens": input_total,
            "output_tokens": output_total,
            "total_tokens": input_total + output_total,
            "by_model": by_model,
            "by_agent": by_agent,
        }

    async def cost_anomalies(
        self,
        *,
        agent_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        threshold_multiplier: float = 3.0,
        limit: int = 10,
    ) -> list[dict]:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        _, from_clause, _ = self._execution_from(filters)

        avg_cost = (
            await self.session.execute(
                select(func.avg(Execution.estimated_cost)).select_from(from_clause).where(where)
            )
        ).scalar() or 0.0

        if avg_cost <= 0:
            return []

        threshold = float(avg_cost) * threshold_multiplier
        stmt = (
            self._execution_base(filters)
            .where(Execution.estimated_cost > threshold)
            .order_by(Execution.estimated_cost.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        executions = result.scalars().all()
        return [
            {
                "execution_id": str(ex.id),
                "agent_id": str(ex.agent_id),
                "model": ex.model,
                "estimated_cost": float(ex.estimated_cost or 0),
                "avg_cost": float(avg_cost),
                "multiplier": round(float(ex.estimated_cost or 0) / float(avg_cost), 2),
                "started_at": ex.started_at.isoformat() if ex.started_at else None,
            }
            for ex in executions
        ]

    async def agent_health_metrics(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict]:
        filters = self._execution_filters(
            workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)

        stmt = (
            select(
                Agent.id,
                Agent.name,
                func.count().label("total_executions"),
                func.avg(
                    case((Execution.status == "success", 1), else_=0)
                ).label("success_rate"),
                func.avg(
                    case((Execution.status == "failed", 1), else_=0)
                ).label("error_rate"),
                func.avg(Execution.latency_ms).label("avg_latency_ms"),
                func.sum(Execution.estimated_cost).label("total_cost"),
                func.avg(Execution.estimated_cost).label("avg_cost"),
            )
            .select_from(Agent)
            .join(Execution, Execution.agent_id == Agent.id)
            .where(where)
            .group_by(Agent.id, Agent.name)
        )
        result = await self.session.execute(stmt)
        metrics = []
        for row in result:
            success_rate = float(row.success_rate or 0) * 100
            error_rate = float(row.error_rate or 0) * 100
            avg_latency = float(row.avg_latency_ms or 0)
            total_cost = float(row.total_cost or 0)
            avg_cost = float(row.avg_cost or 0)
            breakdown = compute_health(
                total_executions=int(row.total_executions or 0),
                success_rate_pct=success_rate,
                error_rate_pct=error_rate,
                avg_latency_ms=avg_latency,
                total_cost=total_cost,
            )

            metrics.append(
                {
                    "agent_id": str(row.id),
                    "agent_name": row.name,
                    "total_executions": row.total_executions,
                    "success_rate": breakdown.success_rate,
                    "error_rate": breakdown.error_rate,
                    "avg_latency_ms": breakdown.avg_latency_ms,
                    "total_cost": breakdown.total_cost,
                    "avg_cost_per_execution": breakdown.avg_cost_per_execution,
                    "health_score": breakdown.health_score,
                    "breakdown": {
                        "latency_score": breakdown.latency_score,
                        "cost_efficiency_score": breakdown.cost_efficiency_score,
                        "reliability_score": breakdown.reliability_score,
                    },
                }
            )
        return sorted(metrics, key=lambda m: m["health_score"], reverse=True)

    async def search_traces(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        model: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Execution], int]:
        filters = self._execution_filters(
            agent_id=agent_id,
            workspace_id=workspace_id,
            model=model,
            status=status,
            start_date=start_date,
            end_date=end_date,
            search=search,
        )
        where = self._where(filters)
        from_clause = (
            Execution.__table__.join(Agent, Agent.id == Execution.agent_id)
            if workspace_id
            else Execution.__table__
        )

        total = (
            await self.session.execute(select(func.count()).select_from(from_clause).where(where))
        ).scalar() or 0

        stmt = (
            select(Execution)
            .options(
                load_only(
                    Execution.id,
                    Execution.agent_id,
                    Execution.status,
                    Execution.latency_ms,
                    Execution.token_usage,
                    Execution.estimated_cost,
                    Execution.model,
                    Execution.output,
                    Execution.started_at,
                    Execution.completed_at,
                )
            )
            .select_from(from_clause)
            .where(where)
            .order_by(Execution.started_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_trace_events(self, execution_id: uuid.UUID) -> list[ExecutionEvent]:
        stmt = (
            select(ExecutionEvent)
            .where(ExecutionEvent.execution_id == execution_id)
            .order_by(ExecutionEvent.timestamp.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def evaluation_trends(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[tuple[str, float]]:
        filters = []
        if workspace_id:
            filters.append(Agent.workspace_id == workspace_id)
        if agent_id:
            filters.append(Evaluation.agent_id == agent_id)
        if start_date:
            filters.append(Evaluation.evaluation_date >= start_date)
        if end_date:
            filters.append(Evaluation.evaluation_date <= end_date)
        where = self._where(filters)

        stmt = (
            select(
                func.date_trunc("day", Evaluation.evaluation_date).label("date"),
                func.avg(Evaluation.score).label("value"),
            )
            .select_from(Evaluation)
            .join(Agent, Agent.id == Evaluation.agent_id)
            .where(where)
            .group_by(text("date"))
            .order_by(text("date"))
        )
        result = await self.session.execute(stmt)
        return [(str(row.date), float(row.value or 0)) for row in result]

    async def monthly_cost(
        self,
        *,
        agent_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> float:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        q = select(func.sum(Execution.estimated_cost))
        if workspace_id:
            q = q.select_from(Execution).join(Agent, Agent.id == Execution.agent_id)
        else:
            q = q.select_from(Execution)
        result = await self.session.execute(q.where(where))
        return float(result.scalar() or 0)

    async def monthly_time_series(
        self,
        *,
        agent_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[tuple[str, float]]:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        stmt = select(
            func.date_trunc("month", Execution.started_at).label("date"),
            func.sum(Execution.estimated_cost).label("value"),
        )
        if workspace_id:
            stmt = stmt.select_from(Execution).join(Agent, Agent.id == Execution.agent_id)
        else:
            stmt = stmt.select_from(Execution)
        stmt = stmt.where(where).group_by(text("date")).order_by(text("date"))
        result = await self.session.execute(stmt)
        return [(str(row.date), float(row.value or 0)) for row in result]

    async def cost_by_workspace(
        self,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
    ) -> list[dict]:
        filters = self._execution_filters(start_date=start_date, end_date=end_date)
        where = self._where(filters)
        stmt = (
            select(
                Workspace.id,
                Workspace.name,
                func.sum(Execution.estimated_cost).label("total_cost"),
                func.count().label("execution_count"),
            )
            .select_from(Execution)
            .join(Agent, Agent.id == Execution.agent_id)
            .join(Workspace, Workspace.id == Agent.workspace_id)
            .where(where)
            .group_by(Workspace.id, Workspace.name)
            .order_by(text("total_cost DESC"))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [
            {
                "workspace_id": str(row.id),
                "workspace_name": row.name,
                "total_cost": float(row.total_cost or 0),
                "execution_count": row.execution_count,
            }
            for row in result
        ]

    async def cached_token_total(
        self,
        *,
        agent_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        q = select(func.sum(func.coalesce(_cached_tokens_expr(), 0)))
        if workspace_id:
            q = q.select_from(Execution).join(Agent, Agent.id == Execution.agent_id)
        else:
            q = q.select_from(Execution)
        return int((await self.session.execute(q.where(where))).scalar() or 0)

    async def token_anomalies(
        self,
        *,
        agent_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        threshold_multiplier: float = 3.0,
        limit: int = 10,
    ) -> list[dict]:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        avg_q = select(func.avg(_token_total_expr()))
        if workspace_id:
            avg_q = avg_q.select_from(Execution).join(Agent, Agent.id == Execution.agent_id)
        else:
            avg_q = avg_q.select_from(Execution)
        avg_tokens = float((await self.session.execute(avg_q.where(where))).scalar() or 0)
        if avg_tokens <= 0:
            return []
        threshold = avg_tokens * threshold_multiplier
        stmt = select(Execution)
        if workspace_id:
            stmt = stmt.join(Agent, Agent.id == Execution.agent_id)
        stmt = stmt.where(where, _token_total_expr() > threshold).order_by(
            _token_total_expr().desc()
        ).limit(limit)
        result = await self.session.execute(stmt)
        rows = []
        for ex in result.scalars().all():
            usage = ex.token_usage or {}
            total = int(usage.get("total_tokens", 0) or 0)
            rows.append(
                {
                    "execution_id": str(ex.id),
                    "agent_id": str(ex.agent_id),
                    "model": ex.model,
                    "total_tokens": total,
                    "avg_tokens": avg_tokens,
                    "multiplier": round(total / avg_tokens, 2),
                    "started_at": ex.started_at.isoformat() if ex.started_at else None,
                }
            )
        return rows

    async def health_trends(
        self,
        *,
        agent_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[tuple[str, float]]:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        stmt = select(
            func.date_trunc("day", Execution.started_at).label("date"),
            func.avg(case((Execution.status == "success", 1), else_=0)).label("success_rate"),
            func.avg(case((Execution.status == "failed", 1), else_=0)).label("error_rate"),
            func.avg(Execution.latency_ms).label("avg_latency"),
            func.avg(Execution.estimated_cost).label("avg_cost"),
            func.count().label("cnt"),
        )
        if workspace_id:
            stmt = stmt.select_from(Execution).join(Agent, Agent.id == Execution.agent_id)
        else:
            stmt = stmt.select_from(Execution)
        stmt = stmt.where(where).group_by(text("date")).order_by(text("date"))
        result = await self.session.execute(stmt)
        points = []
        for row in result:
            cnt = int(row.cnt or 0)
            if cnt == 0:
                continue
            breakdown = compute_health(
                total_executions=cnt,
                success_rate_pct=float(row.success_rate or 0) * 100,
                error_rate_pct=float(row.error_rate or 0) * 100,
                avg_latency_ms=float(row.avg_latency or 0),
                total_cost=float(row.avg_cost or 0) * cnt,
            )
            points.append((str(row.date), breakdown.health_score))
        return points

    async def recent_executions(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 25,
    ) -> list[dict]:
        filters = self._execution_filters(
            workspace_id=workspace_id,
            agent_id=agent_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )
        where = self._where(filters)
        stmt = (
            select(
                Execution.id,
                Execution.agent_id,
                Agent.name.label("agent_name"),
                Agent.provider.label("provider"),
                Agent.environment.label("environment"),
                Execution.status,
                Execution.model,
                Execution.token_usage,
                Execution.latency_ms,
                Execution.estimated_cost,
                Execution.started_at,
            )
            .join(Agent, Agent.id == Execution.agent_id)
            .where(where)
            .order_by(Execution.started_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows: list[dict] = []
        for row in result:
            usage = row.token_usage or {}
            total_tokens = int(usage.get("total_tokens", 0) or 0)
            if not total_tokens:
                total_tokens = int(usage.get("input_tokens", 0) or 0) + int(
                    usage.get("output_tokens", 0) or 0
                )
            exec_id = str(row.id)
            rows.append(
                {
                    "execution_id": exec_id,
                    "trace_id": exec_id,
                    "agent_id": str(row.agent_id),
                    "agent_name": row.agent_name,
                    "provider": row.provider,
                    "environment": row.environment,
                    "status": row.status,
                    "model": row.model,
                    "total_tokens": total_tokens,
                    "latency_ms": row.latency_ms,
                    "estimated_cost": float(row.estimated_cost or 0),
                    "started_at": row.started_at.isoformat() if row.started_at else "",
                }
            )
        return rows

    async def tool_analytics(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict]:
        """Aggregate tool events from execution_events."""
        filters = self._execution_filters(
            workspace_id=workspace_id,
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
        )
        where = self._where(filters)
        stmt = (
            select(
                ExecutionEvent.event_type,
                ExecutionEvent.event_data,
                Execution.estimated_cost,
            )
            .join(Execution, Execution.id == ExecutionEvent.execution_id)
            .join(Agent, Agent.id == Execution.agent_id)
            .where(where)
            .where(
                ExecutionEvent.event_type.ilike("%tool%")
                | ExecutionEvent.event_type.ilike("%function%")
            )
        )
        rows = (await self.session.execute(stmt)).all()
        metrics: dict[str, dict] = {}
        for row in rows:
            data = row.event_data or {}
            tool_name = str(data.get("tool_name") or data.get("name") or data.get("tool") or "unknown")
            bucket = metrics.setdefault(
                tool_name,
                {"invocation_count": 0, "success_count": 0, "failure_count": 0, "latencies": [], "total_cost": 0.0},
            )
            bucket["invocation_count"] += 1
            et = row.event_type.lower()
            if "error" in et or "failed" in et or data.get("error"):
                bucket["failure_count"] += 1
            else:
                bucket["success_count"] += 1
            lat = data.get("latency_ms") or data.get("duration_ms")
            if lat is not None:
                bucket["latencies"].append(int(lat))
            if row.estimated_cost:
                bucket["total_cost"] += float(row.estimated_cost) / max(len(rows), 1)

        result = []
        for name, m in sorted(metrics.items(), key=lambda x: -x[1]["invocation_count"]):
            lats = m["latencies"]
            avg_lat = sum(lats) / len(lats) if lats else 0.0
            p95 = sorted(lats)[int(len(lats) * 0.95)] if lats else 0
            inv = m["invocation_count"]
            succ = m["success_count"]
            result.append(
                {
                    "tool_name": name,
                    "invocation_count": inv,
                    "success_count": succ,
                    "failure_count": m["failure_count"],
                    "success_rate": round((succ / inv) * 100, 1) if inv else 0.0,
                    "avg_latency_ms": round(avg_lat, 1),
                    "total_cost": round(m["total_cost"], 6),
                    "p95_latency_ms": float(p95),
                }
            )
        return result

    # --- Observability dashboard (Helicone/Langfuse-style) ---

    def _date_trunc_expr(self, bucket: str):
        if bucket == "hour":
            return func.date_trunc("hour", Execution.started_at)
        if bucket == "week":
            return func.date_trunc("week", Execution.started_at)
        return func.date_trunc("day", Execution.started_at)

    async def bucketed_time_series(
        self,
        metric: Literal["requests", "cost", "tokens", "latency", "failure_rate"],
        *,
        workspace_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        start_date: datetime,
        end_date: datetime,
        bucket: Optional[str] = None,
    ) -> list[tuple[str, float]]:
        bucket = bucket or resolve_bucket(start_date, end_date)
        filters = self._execution_filters(
            agent_id=agent_id,
            workspace_id=workspace_id,
            start_date=start_date,
            end_date=end_date,
        )
        where = self._where(filters)
        date_expr = self._date_trunc_expr(bucket).label("bucket")

        if metric == "requests":
            value_expr = func.count().label("value")
        elif metric == "cost":
            value_expr = func.coalesce(func.sum(Execution.estimated_cost), 0).label("value")
        elif metric == "tokens":
            value_expr = func.coalesce(func.sum(_token_total_expr()), 0).label("value")
        elif metric == "latency":
            value_expr = func.coalesce(func.avg(Execution.latency_ms), 0).label("value")
        elif metric == "failure_rate":
            value_expr = (
                func.avg(case((Execution.status == "failed", 1), else_=0)) * 100
            ).label("value")
        else:
            raise ValueError(f"Unknown metric: {metric}")

        stmt = select(date_expr, value_expr)
        if workspace_id:
            stmt = stmt.select_from(Execution).join(Agent, Agent.id == Execution.agent_id)
        else:
            stmt = stmt.select_from(Execution)
        stmt = stmt.where(where).group_by(text("bucket")).order_by(text("bucket"))
        result = await self.session.execute(stmt)

        raw: dict[str, float] = {}
        for row in result:
            if row.bucket is None:
                continue
            label = bucket_label(row.bucket, bucket)  # type: ignore[arg-type]
            raw[label] = float(row.value or 0)

        return zero_fill_series(raw, start_date, end_date, bucket)  # type: ignore[arg-type]

    async def top_models(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> list[dict]:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        stmt = select(
            Execution.model,
            func.count().label("request_count"),
            func.coalesce(func.sum(Execution.estimated_cost), 0).label("total_cost"),
            func.coalesce(func.sum(_token_total_expr()), 0).label("total_tokens"),
        )
        if workspace_id:
            stmt = stmt.select_from(Execution).join(Agent, Agent.id == Execution.agent_id)
        else:
            stmt = stmt.select_from(Execution)
        stmt = (
            stmt.where(where, Execution.model.isnot(None))
            .group_by(Execution.model)
            .order_by(text("request_count DESC"))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [
            {
                "model": row.model or "unknown",
                "request_count": int(row.request_count or 0),
                "total_cost": float(row.total_cost or 0),
                "total_tokens": int(row.total_tokens or 0),
            }
            for row in result
        ]

    async def top_agents(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> list[dict]:
        filters = self._execution_filters(
            workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        stmt = (
            select(
                Execution.agent_id,
                Agent.name.label("agent_name"),
                func.count().label("request_count"),
                func.coalesce(func.sum(Execution.estimated_cost), 0).label("total_cost"),
                func.coalesce(func.sum(_token_total_expr()), 0).label("total_tokens"),
                func.avg(case((Execution.status == "success", 1), else_=0)).label("success_rate"),
            )
            .select_from(Execution)
            .join(Agent, Agent.id == Execution.agent_id)
            .where(where)
            .group_by(Execution.agent_id, Agent.name)
            .order_by(text("request_count DESC"))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [
            {
                "agent_id": str(row.agent_id),
                "agent_name": row.agent_name,
                "request_count": int(row.request_count or 0),
                "total_cost": float(row.total_cost or 0),
                "total_tokens": int(row.total_tokens or 0),
                "success_rate": round(float(row.success_rate or 0) * 100, 1),
            }
            for row in result
        ]

    async def top_providers(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> list[dict]:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        provider_expr = func.coalesce(Agent.provider, "unknown")
        stmt = (
            select(
                provider_expr.label("provider"),
                func.count().label("request_count"),
                func.coalesce(func.sum(Execution.estimated_cost), 0).label("total_cost"),
                func.coalesce(func.sum(_token_total_expr()), 0).label("total_tokens"),
            )
            .select_from(Execution)
            .join(Agent, Agent.id == Execution.agent_id)
            .where(where)
            .group_by(provider_expr)
            .order_by(text("request_count DESC"))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [
            {
                "provider": row.provider or "unknown",
                "request_count": int(row.request_count or 0),
                "total_cost": float(row.total_cost or 0),
                "total_tokens": int(row.total_tokens or 0),
            }
            for row in result
        ]

    async def count_active_agents(
        self,
        *,
        workspace_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        filters = self._execution_filters(
            workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        stmt = select(func.count(func.distinct(Execution.agent_id)))
        if workspace_id:
            stmt = stmt.select_from(Execution).join(Agent, Agent.id == Execution.agent_id)
        else:
            stmt = stmt.select_from(Execution)
        return int((await self.session.execute(stmt.where(where))).scalar() or 0)

    async def execution_leaderboard(
        self,
        sort_by: Literal["cost", "latency"],
        *,
        workspace_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> list[dict]:
        filters = self._execution_filters(
            agent_id=agent_id, workspace_id=workspace_id, start_date=start_date, end_date=end_date
        )
        where = self._where(filters)
        order_col = Execution.estimated_cost if sort_by == "cost" else Execution.latency_ms
        stmt = (
            select(
                Execution.id,
                Execution.agent_id,
                Agent.name.label("agent_name"),
                Execution.status,
                Execution.model,
                Execution.latency_ms,
                Execution.estimated_cost,
                Execution.started_at,
            )
            .select_from(Execution)
            .join(Agent, Agent.id == Execution.agent_id)
            .where(where, order_col.isnot(None))
            .order_by(order_col.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [
            {
                "execution_id": str(row.id),
                "agent_id": str(row.agent_id),
                "agent_name": row.agent_name,
                "status": row.status,
                "model": row.model,
                "latency_ms": row.latency_ms,
                "estimated_cost": float(row.estimated_cost or 0),
                "started_at": row.started_at.isoformat() if row.started_at else "",
            }
            for row in result
        ]
