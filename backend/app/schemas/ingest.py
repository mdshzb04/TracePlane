import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class IngestAgentMeta(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    framework: Optional[str] = Field(default=None, max_length=50)
    model: Optional[str] = Field(default=None, max_length=100)
    provider: Optional[str] = Field(default=None, max_length=50)
    environment: Optional[str] = Field(default="production", max_length=50)
    owner: Optional[str] = Field(default=None, max_length=255)
    tags: list[str] = Field(default_factory=list)


class IngestEvent(BaseModel):
    event_type: str = Field(min_length=1, max_length=50)
    event_data: dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None


class IngestSpan(BaseModel):
    span_id: Optional[str] = Field(default=None, max_length=100)
    parent_span_id: Optional[str] = Field(default=None, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    span_type: str = Field(default="custom", pattern=r"^(root|llm|tool|error|custom)$")
    status: str = Field(default="success", pattern=r"^(success|failed|running)$")
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    latency_ms: Optional[int] = Field(default=None, ge=0)
    attributes: dict[str, Any] = Field(default_factory=dict)
    token_usage: dict[str, Any] = Field(default_factory=dict)
    estimated_cost: Optional[float] = Field(default=None, ge=0)


class IngestTraceRequest(BaseModel):
    agent: IngestAgentMeta
    input: Optional[str] = None
    output: Optional[str] = None
    status: str = Field(default="success", pattern=r"^(running|success|failed|timeout|cancelled)$")
    latency_ms: Optional[int] = Field(default=None, ge=0)
    model: Optional[str] = Field(default=None, max_length=100)
    token_usage: dict[str, Any] = Field(default_factory=dict)
    estimated_cost: Optional[float] = Field(default=None, ge=0)
    events: list[IngestEvent] = Field(default_factory=list)
    spans: list[IngestSpan] = Field(default_factory=list)
    trace_id: Optional[str] = Field(default=None, max_length=100)


class DiscoveryInfo(BaseModel):
    framework: str
    model: str
    provider: Optional[str] = None


class IngestTraceResponse(BaseModel):
    agent_id: uuid.UUID
    execution_id: uuid.UUID
    trace_id: uuid.UUID
    created_agent: bool = False
    health_score: float = Field(default=100.0, ge=0, le=100)
    discovery: Optional[DiscoveryInfo] = None
