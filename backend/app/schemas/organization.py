import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class OrganizationRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationMemberRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrganizationMemberCreate(BaseModel):
    user_id: uuid.UUID
    role: str = Field(default="developer", pattern=r"^(viewer|developer|admin)$")
