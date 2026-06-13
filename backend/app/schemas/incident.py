import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class IncidentEventRead(BaseModel):
    id: uuid.UUID
    event_type: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class IncidentRead(BaseModel):
    id: uuid.UUID
    title: str
    incident_type: str
    severity: str
    status: str
    root_cause: Optional[str] = None
    resolution_notes: Optional[str] = None
    agent_id: Optional[uuid.UUID] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    events: list[IncidentEventRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class IncidentUpdate(BaseModel):
    status: Optional[Literal["open", "investigating", "resolved"]] = None
    root_cause: Optional[str] = None
    resolution_notes: Optional[str] = None
