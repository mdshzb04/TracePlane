import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class WorkflowNodeRead(BaseModel):
    kind: str
    label: str
    config: dict[str, str] = Field(default_factory=dict)


class AgentHealthMetrics(BaseModel):
    health_score: float = Field(ge=0, le=100)
    total_executions: int = 0
    success_rate: float = 0.0
    error_rate: float = 0.0
    avg_latency_ms: float = 0.0
    total_cost: float = 0.0


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    owner: str = Field(min_length=1, max_length=255)
    model: Optional[str] = Field(default=None, max_length=100)
    tags: Optional[list[str]] = Field(default=None)
    workflow: Optional[list[WorkflowNodeRead]] = Field(default=None)
    tools: Optional[list[str]] = Field(default=None)


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)
    model: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, pattern=r"^(active|inactive|deprecated)$")
    tags: Optional[list[str]] = None
    workflow: Optional[list[WorkflowNodeRead]] = None
    tools: Optional[list[str]] = None


class AgentRead(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    owner: str
    model: Optional[str] = None
    framework: Optional[str] = None
    environment: Optional[str] = None
    provider: Optional[str] = None
    external_name: Optional[str] = None
    source: str = "sdk"
    status: str
    tags: list[str] = []
    last_seen_at: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def normalize_lists(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data["tags"] = data.get("tags") or []
        return data


class AgentDetailRead(AgentRead):
    health: AgentHealthMetrics


class AgentListParams(BaseModel):
    status: Optional[str] = None
    owner: Optional[str] = None
    search: Optional[str] = None
    tags: Optional[list[str]] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedAgentResponse(BaseModel):
    items: list[AgentRead]
    total: int
    page: int
    page_size: int
    total_pages: int
