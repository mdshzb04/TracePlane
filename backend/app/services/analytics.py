import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import async_session_factory

from app.repositories.analytics import AnalyticsRepository
from app.schemas.analytics import (
    AgentHealth,
    AgentHealthResponse,
    AnalyticsParams,
    CostAnomaly,
    CostAnalyticsResponse,
    CostByAgent,
    CostByModel,
    CostBreakdown,
    CostByWorkspace,
    CostIntelligence,
    CostTimeSeries,
    EvaluationTrend,
    HealthScoreBreakdown,
    LatencyTimeSeries,
    LiveDashboard,
    ModelUsageListResponse,
    ModelUsageSummary,
    OverviewStats,
    ToolAnalyticsResponse,
    ToolMetric,
    TimeSeriesPoint,
    TokenAnalyticsResponse,
    TokenAnomaly,
    TokenByAgent,
    TokenByModel,
    TokenIntelligence,
    TokenUsageTimeSeries,
    TraceDetail,
    TraceEvent,
    TraceListResponse,
    TraceSummary,
    ExecutionTableRow,
    ObservabilityBreakdowns,
    ObservabilityDashboard,
    ObservabilityKpis,
    ObservabilityTables,
    ObservabilityTimeSeries,
    TopAgentRow,
    TopModelRow,
    TopProviderRow,
    TopToolRow,
)
from app.core.cache import cache_key, cached_async
from app.core.time_buckets import resolve_bucket, utc_now
from app.services.live_service import LiveService
from app.services.trace_explorer import TraceExplorerService, build_timelines
from app.services.langfuse_service import langfuse_service

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AnalyticsRepository(session)

    async def get_overview(self, params: AnalyticsParams) -> OverviewStats:
        key = cache_key(
            "overview",
            params.workspace_id,
            params.agent_id,
            params.start_date,
            params.end_date,
        )

        async def _load() -> OverviewStats:
            month_start = datetime.now(timezone.utc).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

            async def _agents():
                async with async_session_factory() as session:
                    return await AnalyticsRepository(session).count_agents(
                        workspace_id=params.workspace_id
                    )

            async def _stats():
                async with async_session_factory() as session:
                    return await AnalyticsRepository(session).execution_stats(
                        agent_id=params.agent_id,
                        workspace_id=params.workspace_id,
                        start_date=params.start_date,
                        end_date=params.end_date,
                    )

            async def _monthly():
                async with async_session_factory() as session:
                    return await AnalyticsRepository(session).monthly_cost(
                        agent_id=params.agent_id,
                        workspace_id=params.workspace_id,
                        start_date=month_start,
                    )

            total_agents, stats, monthly = await asyncio.gather(_agents(), _stats(), _monthly())
            total = stats["total"]
            success_rate = (stats["success"] / total * 100) if total > 0 else 0.0
            error_rate = (stats["failed"] / total * 100) if total > 0 else 0.0

            return OverviewStats(
                total_agents=total_agents,
                total_executions=total,
                success_rate=round(success_rate, 2),
                error_rate=round(error_rate, 2),
                avg_latency_ms=round(stats["avg_latency_ms"], 2),
                total_token_usage=stats["total_tokens"],
                total_estimated_cost=round(stats["total_cost"], 6),
                monthly_cost=round(monthly, 6),
            )

        return await cached_async(key, 30, _load)

    async def get_latency_time_series(self, params: AnalyticsParams) -> LatencyTimeSeries:
        points = await self.repo.daily_time_series(
            "latency",
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        return LatencyTimeSeries(
            points=[TimeSeriesPoint(date=d, value=v) for d, v in points]
        )

    async def get_cost_time_series(self, params: AnalyticsParams) -> CostTimeSeries:
        points = await self.repo.daily_time_series(
            "cost",
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        return CostTimeSeries(points=[TimeSeriesPoint(date=d, value=v) for d, v in points])

    async def get_token_usage_time_series(self, params: AnalyticsParams) -> TokenUsageTimeSeries:
        points = await self.repo.daily_time_series(
            "tokens",
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        return TokenUsageTimeSeries(
            points=[TimeSeriesPoint(date=d, value=v) for d, v in points]
        )

    async def get_evaluation_trends(self, params: AnalyticsParams) -> EvaluationTrend:
        points = await self.repo.evaluation_trends(
            workspace_id=params.workspace_id,
            agent_id=params.agent_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        return EvaluationTrend(points=[TimeSeriesPoint(date=d, value=v) for d, v in points])

    async def get_cost_intelligence(self, params: AnalyticsParams) -> CostIntelligence:
        stats = await self.repo.execution_stats(
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        trends = await self.repo.daily_time_series(
            "cost",
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        by_agent = await self.repo.cost_by_agent(
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        by_model = await self.repo.cost_by_model(
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        anomalies = await self.repo.cost_anomalies(
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = await self.repo.monthly_cost(
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=month_start,
        )

        total = stats["total"]
        cost_per_exec = stats["total_cost"] / total if total > 0 else 0.0

        monthly_trends = await self.repo.monthly_time_series(
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        if params.workspace_id:
            by_workspace = []
        else:
            by_workspace = await self.repo.cost_by_workspace(
                start_date=params.start_date,
                end_date=params.end_date,
            )

        return CostIntelligence(
            total_cost=round(stats["total_cost"], 6),
            monthly_cost=round(monthly, 6),
            cost_per_execution=round(cost_per_exec, 6),
            trends=[TimeSeriesPoint(date=d, value=v) for d, v in trends],
            monthly_trends=[TimeSeriesPoint(date=d, value=v) for d, v in monthly_trends],
            by_agent=[CostByAgent(**a) for a in by_agent],
            by_model=[CostByModel(**m) for m in by_model],
            by_workspace=[CostByWorkspace(**w) for w in by_workspace],
            anomalies=[CostAnomaly(**a) for a in anomalies],
        )

    async def get_token_intelligence(self, params: AnalyticsParams) -> TokenIntelligence:
        breakdown = await self.repo.token_breakdown(
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        trends = await self.repo.daily_time_series(
            "tokens",
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        cached = await self.repo.cached_token_total(
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        token_anomalies = await self.repo.token_anomalies(
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )

        return TokenIntelligence(
            input_tokens=breakdown["input_tokens"],
            output_tokens=breakdown["output_tokens"],
            cached_tokens=cached,
            total_tokens=breakdown["total_tokens"],
            trends=[TimeSeriesPoint(date=d, value=v) for d, v in trends],
            by_model=[TokenByModel(**m) for m in breakdown["by_model"]],
            by_agent=[TokenByAgent(**a) for a in breakdown["by_agent"]],
            anomalies=[TokenAnomaly(**a) for a in token_anomalies],
        )

    async def get_tool_analytics(self, params: AnalyticsParams) -> ToolAnalyticsResponse:
        rows = await self.repo.tool_analytics(
            workspace_id=params.workspace_id,
            agent_id=params.agent_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        tools = [ToolMetric(**r) for r in rows]
        return ToolAnalyticsResponse(
            tools=tools,
            total_invocations=sum(t.invocation_count for t in tools),
            total_failures=sum(t.failure_count for t in tools),
        )

    async def get_agent_health(self, params: AnalyticsParams) -> AgentHealthResponse:
        metrics = await self.repo.agent_health_metrics(
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        agents = [
            AgentHealth(
                **{k: v for k, v in m.items() if k != "breakdown"},
                breakdown=HealthScoreBreakdown(**m["breakdown"]) if m.get("breakdown") else None,
            )
            for m in metrics
        ]
        platform_score = (
            sum(a.health_score for a in agents) / len(agents) if agents else 100.0
        )
        return AgentHealthResponse(
            agents=agents,
            platform_health_score=round(platform_score, 1),
        )

    async def get_trace_explorer(
        self,
        params: AnalyticsParams,
        page: int = 1,
        page_size: int = 20,
    ) -> TraceListResponse:
        from app.models.agent import Agent

        offset = (page - 1) * page_size
        executions, total = await self.repo.search_traces(
            workspace_id=params.workspace_id,
            agent_id=params.agent_id,
            model=params.model,
            status=params.status,
            start_date=params.start_date,
            end_date=params.end_date,
            search=params.search,
            offset=offset,
            limit=page_size,
        )

        agent_names: dict[str, str] = {}
        if executions:
            agent_ids = {ex.agent_id for ex in executions}
            from sqlalchemy import select

            result = await self.session.execute(
                select(Agent.id, Agent.name).where(Agent.id.in_(agent_ids))
            )
            agent_names = {str(row.id): row.name for row in result}

        traces = []
        for ex in executions:
            usage = ex.token_usage or {}
            input_t = int(usage.get("input_tokens", 0) or 0)
            output_t = int(usage.get("output_tokens", 0) or 0)
            total_t = int(usage.get("total_tokens", 0) or input_t + output_t)
            error = ex.output if ex.status in ("failed", "timeout") else None

            traces.append(
                TraceSummary(
                    trace_id=str(ex.id),
                    execution_id=str(ex.id),
                    agent_id=str(ex.agent_id),
                    agent_name=agent_names.get(str(ex.agent_id)),
                    name=f"{agent_names.get(str(ex.agent_id), 'Agent')} execution",
                    model=ex.model,
                    status=ex.status,
                    timestamp=ex.started_at.isoformat() if ex.started_at else "",
                    latency_ms=float(ex.latency_ms) if ex.latency_ms else None,
                    input_tokens=input_t,
                    output_tokens=output_t,
                    total_tokens=total_t,
                    estimated_cost=float(ex.estimated_cost or 0),
                    error=error,
                    metadata={"correlation_id": str(ex.id)},
                )
            )

        return TraceListResponse(
            traces=traces,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_trace_detail(self, execution_id: uuid.UUID, workspace_id: uuid.UUID) -> TraceDetail:
        from app.core.workspace_scope import get_execution_in_workspace
        from app.models.agent import Agent
        from sqlalchemy import select

        execution = await get_execution_in_workspace(self.session, execution_id, workspace_id)

        agent_name = None
        result = await self.session.execute(
            select(Agent.name).where(Agent.id == execution.agent_id)
        )
        agent_name = result.scalar()

        usage = execution.token_usage or {}
        input_t = int(usage.get("input_tokens", 0) or 0)
        output_t = int(usage.get("output_tokens", 0) or 0)
        total_t = int(usage.get("total_tokens", 0) or input_t + output_t)

        trace = TraceSummary(
            trace_id=str(execution.id),
            execution_id=str(execution.id),
            agent_id=str(execution.agent_id),
            agent_name=agent_name,
            name=f"{agent_name or 'Agent'} execution",
            model=execution.model,
            status=execution.status,
            timestamp=execution.started_at.isoformat() if execution.started_at else "",
            latency_ms=float(execution.latency_ms) if execution.latency_ms else None,
            input_tokens=input_t,
            output_tokens=output_t,
            total_tokens=total_t,
            estimated_cost=float(execution.estimated_cost or 0),
            error=execution.output if execution.status in ("failed", "timeout") else None,
            metadata={"correlation_id": str(execution.id)},
        )

        events_raw = await self.repo.get_trace_events(execution_id)
        events = [
            TraceEvent(
                id=str(e.id),
                event_type=e.event_type,
                timestamp=e.timestamp.isoformat() if e.timestamp else "",
                event_data=e.event_data or {},
            )
            for e in events_raw
        ]

        explorer = TraceExplorerService(self.session)
        spans = await explorer.get_span_tree(execution_id)
        timelines = build_timelines(events)

        return TraceDetail(
            trace=trace,
            input=execution.input,
            output=execution.output,
            events=events,
            spans=spans,
            timelines=timelines,
            correlation_id=str(execution.id),
        )

    async def _failure_trends(self, params: AnalyticsParams) -> list[TimeSeriesPoint]:
        from sqlalchemy import case, func, select, text

        from app.models.execution import Execution

        fail_filters = self.repo._execution_filters(
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        fail_where = self.repo._where(fail_filters)
        _, from_clause, _ = self.repo._execution_from(fail_filters)
        stmt = (
            select(
                func.date_trunc("day", Execution.started_at).label("date"),
                func.avg(case((Execution.status == "failed", 1), else_=0)).label("value"),
            )
            .select_from(from_clause)
            .where(fail_where)
            .group_by(text("date"))
            .order_by(text("date"))
        )
        result = await self.session.execute(stmt)
        return [
            TimeSeriesPoint(date=str(row.date), value=round(float(row.value or 0) * 100, 2))
            for row in result
        ]

    async def get_live_dashboard(self, params: AnalyticsParams) -> LiveDashboard:
        return await LiveService(self.session).get_live_dashboard(params)

    async def get_observability_dashboard(self, params: AnalyticsParams) -> ObservabilityDashboard:
        end = params.end_date or utc_now()
        start = params.start_date or (end - timedelta(days=7))
        bucket = resolve_bucket(start, end)

        key = cache_key(
            "observability",
            params.workspace_id,
            params.agent_id,
            start.isoformat(),
            end.isoformat(),
        )

        async def _empty_dashboard() -> ObservabilityDashboard:
            empty_kpis = ObservabilityKpis(
                total_requests=0,
                total_cost=0,
                total_tokens=0,
                success_rate=0,
                avg_latency_ms=0,
                active_agents=0,
            )
            return ObservabilityDashboard(
                kpis=empty_kpis,
                timeseries=ObservabilityTimeSeries(
                    requests=[], cost=[], tokens=[], latency=[], failure_rate=[], bucket=bucket
                ),
                breakdowns=ObservabilityBreakdowns(top_models=[], top_agents=[], top_providers=[]),
                tables=ObservabilityTables(recent_executions=[]),
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                bucket=bucket,
            )

        async def _load() -> ObservabilityDashboard:
            scoped = AnalyticsParams(
                workspace_id=params.workspace_id,
                agent_id=params.agent_id,
                start_date=start,
                end_date=end,
            )

            async with async_session_factory() as session:
                probe = await AnalyticsRepository(session).execution_stats(
                    agent_id=scoped.agent_id,
                    workspace_id=scoped.workspace_id,
                    start_date=start,
                    end_date=end,
                )
                if probe["total"] == 0:
                    return await _empty_dashboard()

            async def _series(metric: str, svc: AnalyticsService):
                pts = await svc.repo.bucketed_time_series(
                    metric,  # type: ignore[arg-type]
                    workspace_id=scoped.workspace_id,
                    agent_id=scoped.agent_id,
                    start_date=start,
                    end_date=end,
                    bucket=bucket,
                )
                return [TimeSeriesPoint(date=d, value=round(v, 4 if metric == "cost" else 2)) for d, v in pts]

            async def _kpis(svc: AnalyticsService):
                stats = await svc.repo.execution_stats(
                    agent_id=scoped.agent_id,
                    workspace_id=scoped.workspace_id,
                    start_date=start,
                    end_date=end,
                )
                active = await svc.repo.count_active_agents(
                    workspace_id=scoped.workspace_id,
                    start_date=start,
                    end_date=end,
                )
                total = stats["total"]
                success_rate = (stats["success"] / total * 100) if total > 0 else 0.0
                return ObservabilityKpis(
                    total_requests=total,
                    total_cost=round(stats["total_cost"], 6),
                    total_tokens=stats["total_tokens"],
                    success_rate=round(success_rate, 2),
                    avg_latency_ms=round(stats["avg_latency_ms"], 2),
                    active_agents=active,
                )

            async def _breakdowns(svc: AnalyticsService):
                top_models = await svc.repo.top_models(
                    workspace_id=scoped.workspace_id,
                    agent_id=scoped.agent_id,
                    start_date=start,
                    end_date=end,
                )
                top_agents = await svc.repo.top_agents(
                    workspace_id=scoped.workspace_id,
                    start_date=start,
                    end_date=end,
                )
                top_providers = await svc.repo.top_providers(
                    workspace_id=scoped.workspace_id,
                    agent_id=scoped.agent_id,
                    start_date=start,
                    end_date=end,
                )
                return ObservabilityBreakdowns(
                    top_models=[TopModelRow(**m) for m in top_models],
                    top_agents=[TopAgentRow(**a) for a in top_agents],
                    top_providers=[TopProviderRow(**p) for p in top_providers],
                )

            async def _tables(svc: AnalyticsService):
                recent = await svc.repo.recent_executions(
                    workspace_id=scoped.workspace_id,
                    agent_id=scoped.agent_id,
                    start_date=start,
                    end_date=end,
                    limit=25,
                )
                return ObservabilityTables(
                    recent_executions=[ExecutionTableRow(**r) for r in recent],
                )

            async def _load_kpis_tables():
                async with async_session_factory() as session:
                    svc = AnalyticsService(session)
                    kpis = await _kpis(svc)
                    tables = await _tables(svc)
                    return kpis, tables

            async def _load_series():
                async with async_session_factory() as session:
                    svc = AnalyticsService(session)
                    requests = await _series("requests", svc)
                    cost = await _series("cost", svc)
                    tokens = await _series("tokens", svc)
                    latency = await _series("latency", svc)
                    failure_rate = await _series("failure_rate", svc)
                    return requests, cost, tokens, latency, failure_rate

            async def _load_breakdowns():
                async with async_session_factory() as session:
                    return await _breakdowns(AnalyticsService(session))

            (kpis_tables, series, breakdowns) = await asyncio.gather(
                _load_kpis_tables(),
                _load_series(),
                _load_breakdowns(),
            )
            kpis, tables = kpis_tables
            requests, cost, tokens, latency, failure_rate = series

            return ObservabilityDashboard(
                kpis=kpis,
                timeseries=ObservabilityTimeSeries(
                    requests=requests,
                    cost=cost,
                    tokens=tokens,
                    latency=latency,
                    failure_rate=failure_rate,
                    bucket=bucket,
                ),
                breakdowns=breakdowns,
                tables=tables,
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                bucket=bucket,
            )

        return await cached_async(key, 30, _load)

    # --- Langfuse passthrough ---

    async def get_traces(
        self,
        page: int = 1,
        page_size: int = 20,
        tags: Optional[list[str]] = None,
        user_id: Optional[str] = None,
    ) -> TraceListResponse:
        if not langfuse_service.is_enabled():
            return await self.get_trace_explorer(AnalyticsParams(), page=page, page_size=page_size)

        try:
            traces_data = langfuse_service.fetch_traces(
                page=page, limit=page_size, tags=tags, user_id=user_id
            )
            traces = []
            for trace in traces_data.data:
                traces.append(
                    TraceSummary(
                        trace_id=trace.id,
                        execution_id=trace.id,
                        agent_id="",
                        name=trace.name or "Unnamed",
                        timestamp=trace.timestamp.isoformat() if trace.timestamp else "",
                        latency_ms=float(trace.latency) if trace.latency else None,
                        status="completed",
                        tags=trace.tags or [],
                        metadata=trace.metadata or {},
                    )
                )
            total = traces_data.meta.total_items if traces_data.meta else len(traces)
            return TraceListResponse(traces=traces, total=total, page=page, page_size=page_size)
        except Exception as e:
            logger.error("Langfuse traces failed, falling back to DB: %s", e)
            result = await self.get_trace_explorer(AnalyticsParams(), page=page, page_size=page_size)
            result.degraded = True
            return result

    async def get_model_usage(self) -> ModelUsageListResponse:
        breakdown = await self.repo.cost_by_model()
        models = [
            ModelUsageSummary(
                model=m["model"],
                total_calls=m["execution_count"],
                total_input_tokens=0,
                total_output_tokens=0,
                total_tokens=m["total_tokens"],
                total_cost=m["total_cost"],
                avg_latency_ms=0.0,
            )
            for m in breakdown
        ]
        if langfuse_service.is_enabled():
            try:
                return await self._langfuse_model_usage()
            except Exception as e:
                logger.error("Langfuse model usage failed: %s", e)
        return ModelUsageListResponse(models=models, total_models=len(models))

    async def _langfuse_model_usage(self) -> ModelUsageListResponse:
        generations_data = langfuse_service.fetch_generations(limit=1000)
        model_stats: dict[str, dict] = {}
        for gen in generations_data.data:
            model = gen.model or "unknown"
            if model not in model_stats:
                model_stats[model] = {
                    "model": model,
                    "total_calls": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_latency_ms": 0.0,
                }
            stats = model_stats[model]
            stats["total_calls"] += 1
            usage = getattr(gen, "usage", None) or {}
            input_tokens = usage.get("input", 0) if isinstance(usage, dict) else getattr(usage, "input", 0) or 0
            output_tokens = usage.get("output", 0) if isinstance(usage, dict) else getattr(usage, "output", 0) or 0
            stats["total_input_tokens"] += input_tokens
            stats["total_output_tokens"] += output_tokens
            stats["total_tokens"] += input_tokens + output_tokens
            cost = getattr(gen, "calculated_total_cost", None) or getattr(gen, "total_cost", None)
            if cost:
                stats["total_cost"] += float(cost)
        models = [
            ModelUsageSummary(
                model=s["model"],
                total_calls=s["total_calls"],
                total_input_tokens=s["total_input_tokens"],
                total_output_tokens=s["total_output_tokens"],
                total_tokens=s["total_tokens"],
                total_cost=round(s["total_cost"], 6),
                avg_latency_ms=0.0,
            )
            for s in model_stats.values()
        ]
        return ModelUsageListResponse(models=models, total_models=len(models))

    async def get_cost_analytics(self) -> CostAnalyticsResponse:
        intel = await self.get_cost_intelligence(AnalyticsParams())
        return CostAnalyticsResponse(
            total_cost=intel.total_cost,
            cost_by_model={m.model: m.total_cost for m in intel.by_model},
            cost_over_time=[
                CostBreakdown(date=p.date, model="all", cost=p.value, calls=0)
                for p in intel.trends
            ],
        )

    async def get_token_analytics(self) -> TokenAnalyticsResponse:
        intel = await self.get_token_intelligence(AnalyticsParams())
        return TokenAnalyticsResponse(
            total_tokens=intel.total_tokens,
            total_input_tokens=intel.input_tokens,
            total_output_tokens=intel.output_tokens,
            tokens_by_model={m.model: m.total_tokens for m in intel.by_model},
            tokens_over_time=intel.trends,
        )

    async def get_leaderboard(self, params: AnalyticsParams) -> "AgentLeaderboard":
        from app.core.format import format_cost
        from app.schemas.analytics import AgentLeaderboard, LeaderboardEntry

        metrics = await self.repo.agent_health_metrics(
            workspace_id=params.workspace_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )

        eval_scores: dict[str, float] = {}
        try:
            from sqlalchemy import func, select
            from app.models.evaluation_dataset import EvaluationRun

            stmt = (
                select(EvaluationRun.agent_id, func.avg(EvaluationRun.average_score).label("avg_score"))
                .group_by(EvaluationRun.agent_id)
            )
            rows = await self.session.execute(stmt)
            for row in rows:
                if row.avg_score is not None:
                    eval_scores[str(row.agent_id)] = float(row.avg_score)
        except Exception:
            pass

        entries: list[LeaderboardEntry] = []
        for idx, m in enumerate(metrics):
            eval_score = eval_scores.get(m["agent_id"])
            cost_eff = m.get("breakdown", {}).get("cost_efficiency_score", 50.0)
            composite = (
                m["health_score"] * 0.35
                + m["success_rate"] * 0.25
                + cost_eff * 0.2
                + max(0, 100 - m["avg_latency_ms"] / 100) * 0.1
                + (eval_score or 0.5) * 100 * 0.1
            )
            entries.append(
                LeaderboardEntry(
                    rank=idx + 1,
                    agent_id=m["agent_id"],
                    agent_name=m["agent_name"],
                    health_score=m["health_score"],
                    success_rate=m["success_rate"],
                    cost_efficiency_score=cost_eff,
                    avg_latency_ms=m["avg_latency_ms"],
                    total_cost=format_cost(m["total_cost"]) or 0.0,
                    evaluation_score=eval_score,
                    composite_score=round(composite, 1),
                )
            )

        entries.sort(key=lambda e: e.composite_score, reverse=True)
        entries = [e.model_copy(update={"rank": i + 1}) for i, e in enumerate(entries)]

        return AgentLeaderboard(items=entries, total=len(entries))
