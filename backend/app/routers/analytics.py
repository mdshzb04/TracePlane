import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.core.dependencies import DbSession, ViewerUser
from app.schemas.analytics import (
    AgentHealthResponse,
    AnalyticsParams,
    CostAnalyticsResponse,
    CostIntelligence,
    CostTimeSeries,
    EvaluationTrend,
    LatencyTimeSeries,
    LiveDashboard,
    ModelUsageListResponse,
    OverviewStats,
    ObservabilityDashboard,
    ToolAnalyticsResponse,
    TokenAnalyticsResponse,
    TokenIntelligence,
    TokenUsageTimeSeries,
    TraceDetail,
    TraceListResponse,
)
from app.core.workspace_scope import workspace_for_user
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _params(
    workspace_id: uuid.UUID,
    agent_id: Optional[uuid.UUID] = None,
    model: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
) -> AnalyticsParams:
    return AnalyticsParams(
        workspace_id=workspace_id,
        agent_id=agent_id,
        model=model,
        status=status,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )


async def _workspace_id(user: ViewerUser, db: DbSession) -> uuid.UUID:
    return await workspace_for_user(db, user)


@router.get("/overview", response_model=OverviewStats)
async def get_overview(
    current_user: ViewerUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
):
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_overview(_params(ws, agent_id, None, None, start_date, end_date))


@router.get("/live", response_model=LiveDashboard)
async def get_live_dashboard(
    current_user: ViewerUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
):
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_live_dashboard(_params(ws, agent_id))


@router.get("/observability", response_model=ObservabilityDashboard)
async def get_observability_dashboard(
    current_user: ViewerUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
):
    """Helicone/Langfuse-style observability: KPIs, zero-filled time series, breakdowns, tables."""
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_observability_dashboard(
        _params(ws, agent_id, None, None, start_date, end_date)
    )


@router.get("/latency", response_model=LatencyTimeSeries)
async def get_latency(
    current_user: ViewerUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
):
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_latency_time_series(_params(ws, agent_id, None, None, start_date, end_date))


@router.get("/costs", response_model=CostIntelligence)
async def get_costs(
    current_user: ViewerUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
):
    """Cost intelligence: per-execution, per-agent, per-model, trends, and anomalies."""
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_cost_intelligence(_params(ws, agent_id, None, None, start_date, end_date))


@router.get("/costs/timeseries", response_model=CostTimeSeries)
async def get_cost_timeseries(
    current_user: ViewerUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
):
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_cost_time_series(_params(ws, agent_id, None, None, start_date, end_date))


@router.get("/tokens", response_model=TokenIntelligence)
async def get_token_usage(
    current_user: ViewerUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
):
    """Token intelligence: input/output breakdown, per-model, per-agent, trends."""
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_token_intelligence(_params(ws, agent_id, None, None, start_date, end_date))


@router.get("/tokens/timeseries", response_model=TokenUsageTimeSeries)
async def get_token_timeseries(
    current_user: ViewerUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
):
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_token_usage_time_series(_params(ws, agent_id, None, None, start_date, end_date))


@router.get("/tools", response_model=ToolAnalyticsResponse)
async def get_tool_analytics(
    current_user: ViewerUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
):
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_tool_analytics(_params(ws, agent_id, None, None, start_date, end_date))


@router.get("/health", response_model=AgentHealthResponse)
async def get_agent_health(
    current_user: ViewerUser,
    db: DbSession,
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
):
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_agent_health(_params(ws, None, None, None, start_date, end_date))


@router.get("/evaluations", response_model=EvaluationTrend)
async def get_evaluation_trends(
    current_user: ViewerUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
):
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_evaluation_trends(_params(ws, agent_id, None, None, start_date, end_date))


@router.get("/traces", response_model=TraceListResponse)
async def get_traces(
    current_user: ViewerUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    agent_id: Optional[uuid.UUID] = Query(default=None),
    model: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags (Langfuse)"),
    user_id: Optional[str] = Query(default=None),
):
    """Helicone-style trace explorer with search, filtering, and time range."""
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    params = _params(ws, agent_id, model, status, start_date, end_date, search)
    return await service.get_trace_explorer(params, page=page, page_size=page_size)


@router.get("/traces/{execution_id}", response_model=TraceDetail)
async def get_trace_detail(
    execution_id: uuid.UUID,
    current_user: ViewerUser,
    db: DbSession,
):
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_trace_detail(execution_id, workspace_id=ws)


@router.get("/models", response_model=ModelUsageListResponse)
async def get_model_usage(current_user: ViewerUser, db: DbSession):
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_model_usage(_params(ws))


@router.get("/costs/breakdown", response_model=CostAnalyticsResponse)
async def get_cost_breakdown(current_user: ViewerUser, db: DbSession):
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_cost_analytics(_params(ws))


@router.get("/tokens/breakdown", response_model=TokenAnalyticsResponse)
async def get_token_breakdown(current_user: ViewerUser, db: DbSession):
    ws = await _workspace_id(current_user, db)
    service = AnalyticsService(db)
    return await service.get_token_analytics(_params(ws))

