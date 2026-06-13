import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OverviewStats(BaseModel):
    total_agents: int
    total_executions: int
    success_rate: float
    error_rate: float = 0.0
    avg_latency_ms: float
    total_token_usage: int
    total_estimated_cost: float
    monthly_cost: float = 0.0
    degraded: bool = False


class TimeSeriesPoint(BaseModel):
    date: str
    value: float


class LatencyTimeSeries(BaseModel):
    points: list[TimeSeriesPoint]


class CostTimeSeries(BaseModel):
    points: list[TimeSeriesPoint]


class TokenUsageTimeSeries(BaseModel):
    points: list[TimeSeriesPoint]


class EvaluationTrend(BaseModel):
    points: list[TimeSeriesPoint]


class AnalyticsParams(BaseModel):
    agent_id: Optional[uuid.UUID] = None
    workspace_id: Optional[uuid.UUID] = None
    model: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None


# --- Cost Intelligence ---

class CostByAgent(BaseModel):
    agent_id: str
    agent_name: str
    total_cost: float
    execution_count: int


class CostByModel(BaseModel):
    model: str
    total_cost: float
    execution_count: int
    total_tokens: int = 0


class CostAnomaly(BaseModel):
    execution_id: str
    agent_id: str
    model: Optional[str] = None
    estimated_cost: float
    avg_cost: float
    multiplier: float
    started_at: Optional[str] = None


class CostByWorkspace(BaseModel):
    workspace_id: str
    workspace_name: str
    total_cost: float
    execution_count: int


class CostIntelligence(BaseModel):
    total_cost: float
    monthly_cost: float
    cost_per_execution: float
    trends: list[TimeSeriesPoint]
    monthly_trends: list[TimeSeriesPoint] = []
    by_agent: list[CostByAgent]
    by_model: list[CostByModel]
    by_workspace: list[CostByWorkspace] = []
    anomalies: list[CostAnomaly]
    degraded: bool = False


# --- Token Intelligence ---

class TokenByModel(BaseModel):
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int


class TokenByAgent(BaseModel):
    agent_id: str
    agent_name: str
    total_tokens: int


class TokenAnomaly(BaseModel):
    execution_id: str
    agent_id: str
    model: Optional[str] = None
    total_tokens: int
    avg_tokens: float
    multiplier: float
    started_at: Optional[str] = None


class TokenIntelligence(BaseModel):
    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0
    total_tokens: int
    trends: list[TimeSeriesPoint]
    by_model: list[TokenByModel]
    by_agent: list[TokenByAgent]
    anomalies: list[TokenAnomaly] = []
    degraded: bool = False


# --- Agent Health ---

class HealthScoreBreakdown(BaseModel):
    latency_score: float = Field(ge=0, le=100)
    cost_efficiency_score: float = Field(ge=0, le=100)
    reliability_score: float = Field(ge=0, le=100)


class AgentHealth(BaseModel):
    agent_id: str
    agent_name: str
    total_executions: int
    success_rate: float
    error_rate: float
    avg_latency_ms: float
    total_cost: float
    avg_cost_per_execution: float
    health_score: float = Field(ge=0, le=100)
    breakdown: Optional[HealthScoreBreakdown] = None


class AgentHealthResponse(BaseModel):
    agents: list[AgentHealth]
    platform_health_score: float = Field(ge=0, le=100)
    degraded: bool = False


# --- Trace Explorer ---

class TraceSummary(BaseModel):
    trace_id: str
    execution_id: str
    agent_id: str
    agent_name: Optional[str] = None
    name: str
    model: Optional[str] = None
    status: str
    timestamp: str
    latency_ms: Optional[float] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    error: Optional[str] = None
    tags: list[str] = []
    metadata: dict = {}


class TraceListResponse(BaseModel):
    traces: list[TraceSummary]
    total: int
    page: int
    page_size: int
    degraded: bool = False


class TraceEvent(BaseModel):
    id: str
    event_type: str
    timestamp: str
    event_data: dict = {}


class TraceSpanNode(BaseModel):
    id: str
    parent_span_id: Optional[str] = None
    name: str
    span_type: str
    status: str
    started_at: str
    ended_at: Optional[str] = None
    latency_ms: Optional[int] = None
    attributes: dict = {}
    token_usage: dict = {}
    estimated_cost: Optional[float] = None
    children: list["TraceSpanNode"] = []


class TraceTimelines(BaseModel):
    llm_calls: list[TraceEvent] = []
    tool_calls: list[TraceEvent] = []
    errors: list[TraceEvent] = []


class TraceDetail(BaseModel):
    trace: TraceSummary
    input: Optional[str] = None
    output: Optional[str] = None
    events: list[TraceEvent] = []
    spans: list[TraceSpanNode] = []
    timelines: TraceTimelines = Field(default_factory=TraceTimelines)
    correlation_id: Optional[str] = None


# --- Langfuse passthrough (legacy) ---

class ModelUsageSummary(BaseModel):
    model: str
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost: float
    avg_latency_ms: float


class ModelUsageListResponse(BaseModel):
    models: list[ModelUsageSummary]
    total_models: int
    degraded: bool = False


class CostBreakdown(BaseModel):
    date: str
    model: str
    cost: float
    calls: int


class CostAnalyticsResponse(BaseModel):
    total_cost: float
    cost_by_model: dict[str, float]
    cost_over_time: list[CostBreakdown]
    degraded: bool = False


class TokenAnalyticsResponse(BaseModel):
    total_tokens: int
    total_input_tokens: int
    total_output_tokens: int
    tokens_by_model: dict[str, int]
    tokens_over_time: list[TimeSeriesPoint]
    degraded: bool = False


# --- Production Dashboard ---

class LiveExecutionSummary(BaseModel):
    execution_id: str
    agent_id: str
    agent_name: Optional[str] = None
    status: str
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    estimated_cost: float = 0.0
    started_at: str


class LiveTopProvider(BaseModel):
    provider: str
    request_count: int


class LiveTopModel(BaseModel):
    model: str
    request_count: int


class LiveDashboard(BaseModel):
    recent_executions: list[LiveExecutionSummary] = []
    running_executions: list[LiveExecutionSummary] = []
    failed_executions: list[LiveExecutionSummary] = []
    success_rate: float = 0.0
    error_rate: float = 0.0
    avg_latency_ms: float = 0.0
    executions_today: int = 0
    cost_today: float = 0.0
    tokens_today: int = 0
    input_tokens_today: int = 0
    output_tokens_today: int = 0
    active_agents: int = 0
    top_providers: list[LiveTopProvider] = []
    top_models: list[LiveTopModel] = []


class LeaderboardEntry(BaseModel):
    rank: int
    agent_id: str
    agent_name: str
    health_score: float
    success_rate: float
    cost_efficiency_score: float
    avg_latency_ms: float
    total_cost: float
    evaluation_score: Optional[float] = None
    composite_score: float


class AgentLeaderboard(BaseModel):
    items: list[LeaderboardEntry]
    total: int


# --- Tool Analytics (P10) ---

class ToolMetric(BaseModel):
    tool_name: str
    invocation_count: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_latency_ms: float
    total_cost: float
    p95_latency_ms: float = 0.0


class ToolAnalyticsResponse(BaseModel):
    tools: list[ToolMetric]
    total_invocations: int
    total_failures: int


# --- Observability dashboard ---

class ObservabilityKpis(BaseModel):
    total_requests: int
    total_cost: float
    total_tokens: int
    success_rate: float
    avg_latency_ms: float
    active_agents: int


class ObservabilityTimeSeries(BaseModel):
    requests: list[TimeSeriesPoint]
    cost: list[TimeSeriesPoint]
    tokens: list[TimeSeriesPoint]
    latency: list[TimeSeriesPoint]
    failure_rate: list[TimeSeriesPoint]
    bucket: str


class TopModelRow(BaseModel):
    model: str
    request_count: int
    total_cost: float
    total_tokens: int


class TopAgentRow(BaseModel):
    agent_id: str
    agent_name: str
    request_count: int
    total_cost: float
    total_tokens: int
    success_rate: float


class TopToolRow(BaseModel):
    tool_name: str
    invocation_count: int
    success_rate: float
    avg_latency_ms: float
    total_cost: float


class ExecutionTableRow(BaseModel):
    execution_id: str
    trace_id: str
    agent_id: str
    agent_name: str
    provider: Optional[str] = None
    status: str
    model: Optional[str] = None
    total_tokens: int = 0
    latency_ms: Optional[int] = None
    estimated_cost: float = 0.0
    started_at: str


class TopProviderRow(BaseModel):
    provider: str
    request_count: int
    total_cost: float
    total_tokens: int


class ObservabilityBreakdowns(BaseModel):
    top_models: list[TopModelRow]
    top_agents: list[TopAgentRow]
    top_providers: list[TopProviderRow]


class ObservabilityTables(BaseModel):
    recent_executions: list[ExecutionTableRow]


class ObservabilityDashboard(BaseModel):
    kpis: ObservabilityKpis
    timeseries: ObservabilityTimeSeries
    breakdowns: ObservabilityBreakdowns
    tables: ObservabilityTables
    start_date: str
    end_date: str
    bucket: str
    degraded: bool = False
