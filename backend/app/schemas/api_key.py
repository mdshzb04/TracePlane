import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ApiKeyRead(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    workspace_id: uuid.UUID
    is_active: bool
    last_used_at: Optional[datetime] = None
    request_count: int = 0
    total_cost: float = 0.0
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreateResponse(ApiKeyRead):
    key: str  # full key shown once at creation
