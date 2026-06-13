import uuid
from typing import Any, Optional

from typing_extensions import TypedDict


class ExecutionRecord(TypedDict, total=False):
    id: str
    agent_id: str
    input: Optional[str]
    output: Optional[str]
    status: str
    latency_ms: Optional[int]
    token_usage: Optional[dict[str, Any]]
    estimated_cost: Optional[float]
    model: Optional[str]
    started_at: str
    completed_at: Optional[str]


class EventRecord(TypedDict, total=False):
    id: str
    execution_id: str
    event_type: str
    event_data: Optional[dict[str, Any]]
    timestamp: str


class AgentRecord(TypedDict, total=False):
    id: str
    name: str
    description: Optional[str]
    owner: str
    model: Optional[str]
    status: str


class FailureAnalysis(TypedDict, total=False):
    total_failures: int
    failure_rate: float
    failure_types: dict[str, int]
    most_common_error: Optional[str]
    affected_executions: list[str]


class LatencyAnalysis(TypedDict, total=False):
    avg_latency_ms: float
    p50_latency_ms: float
    p90_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    spike_count: int
    spike_threshold_ms: float
    spikes: list[dict[str, Any]]


class CostAnalysis(TypedDict, total=False):
    total_cost: float
    avg_cost_per_execution: float
    max_cost_execution: Optional[dict[str, Any]]
    cost_trend: list[dict[str, Any]]
    anomalies: list[dict[str, Any]]


class PromptAnalysis(TypedDict, total=False):
    version_stats: list[dict[str, Any]]
    regression_count: int
    regressions: list[dict[str, Any]]


class InvestigatorState(TypedDict, total=False):
    query: str
    agent_id: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    agent_info: Optional[AgentRecord]
    executions: list[ExecutionRecord]
    events: list[EventRecord]
    failure_analysis: Optional[FailureAnalysis]
    latency_analysis: Optional[LatencyAnalysis]
    cost_analysis: Optional[CostAnalysis]
    prompt_analysis: Optional[PromptAnalysis]
    report: Optional[str]
    confidence_score: Optional[float]
    root_causes: Optional[list[dict[str, Any]]]
    recommendations: Optional[list[dict[str, Any]]]