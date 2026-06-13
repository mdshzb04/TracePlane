import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_serializer

from app.core.format import format_cost
from app.schemas.analytics import TraceSpanNode, TraceTimelines


class ExecutionCreate(BaseModel):
    agent_id: uuid.UUID
    input: Optional[str] = None
    model: Optional[str] = Field(default=None, max_length=100)


class ExecutionUpdate(BaseModel):
    output: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern=r"^(running|success|failed|timeout|cancelled)$")
    latency_ms: Optional[int] = Field(default=None, ge=0)
    token_usage: Optional[dict[str, Any]] = None
    estimated_cost: Optional[float] = Field(default=None, ge=0)
    completed_at: Optional[datetime] = None


class ExecutionRead(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    agent_name: Optional[str] = None
    provider: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None
    status: str
    latency_ms: Optional[int] = None
    token_usage: Optional[dict[str, Any]] = None
    estimated_cost: Optional[float] = None
    model: Optional[str] = None
    replay_of_id: Optional[uuid.UUID] = None
    is_replay: bool = False
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("estimated_cost")
    def serialize_cost(self, value: Optional[float]) -> Optional[float]:
        return format_cost(value)


class ExecutionListParams(BaseModel):
    agent_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    search: Optional[str] = None
    sort_by: Literal["started_at", "latency_ms", "estimated_cost", "total_tokens"] = "started_at"
    sort_order: Literal["asc", "desc"] = "desc"
    min_cost: Optional[float] = Field(default=None, ge=0)
    max_cost: Optional[float] = Field(default=None, ge=0)
    min_latency: Optional[int] = Field(default=None, ge=0)
    max_latency: Optional[int] = Field(default=None, ge=0)
    min_tokens: Optional[int] = Field(default=None, ge=0)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ExecutionSummary(BaseModel):
    total_executions: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    avg_latency_ms: float = 0.0
    success_count: int = 0
    failed_count: int = 0


class PaginatedExecutionResponse(BaseModel):
    items: list[ExecutionRead]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary: ExecutionSummary


class ExecutionDetailRead(ExecutionRead):
    agent_name: Optional[str] = None
    spans: list[TraceSpanNode] = Field(default_factory=list)
    timelines: Optional[TraceTimelines] = None
    retry_count: int = 0
    error_count: int = 0


class ReplayMetrics(BaseModel):
    execution_id: uuid.UUID
    output: Optional[str] = None
    latency_ms: Optional[int] = None
    total_tokens: int = 0
    estimated_cost: Optional[float] = None
    status: str

    @field_serializer("estimated_cost")
    def serialize_cost(self, value: Optional[float]) -> Optional[float]:
        return format_cost(value)


class ReplayDiff(BaseModel):
    original: ReplayMetrics
    replay: ReplayMetrics
    output_changed: bool = False
    output_diff: Optional[str] = None
    latency_increased: bool = False
    tokens_increased: bool = False
    cost_increased: bool = False
    quality_dropped: bool = False
    regression_warnings: list[str] = Field(default_factory=list)


class ReplayResponse(BaseModel):
    replay_execution_id: uuid.UUID
    diff: ReplayDiff
    replay_mode: str = Field(default="llm", pattern=r"^(llm|unavailable)$")


class ExecutionEventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=50)
    event_data: Optional[dict[str, Any]] = None


class ExecutionEventRead(BaseModel):
    id: uuid.UUID
    execution_id: uuid.UUID
    event_type: str
    event_data: Optional[dict[str, Any]] = None
    timestamp: datetime

    model_config = {"from_attributes": True}
