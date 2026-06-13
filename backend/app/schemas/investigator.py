import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RootCause(BaseModel):
    category: str
    description: str
    evidence: list[str]
    severity: str = Field(pattern=r"^(low|medium|high|critical)$")


class Recommendation(BaseModel):
    title: str
    description: str
    priority: str = Field(pattern=r"^(low|medium|high|critical)$")


class InvestigationReport(BaseModel):
    summary: str
    confidence_score: float = Field(ge=0, le=1)
    root_causes: list[RootCause]
    recommendations: list[Recommendation]
    agent_id: Optional[uuid.UUID] = None
    query: str
    investigated_at: datetime
    report_source: str = Field(default="rule_based", pattern=r"^(llm|rule_based)$")


class InvestigateRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    agent_id: Optional[uuid.UUID] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class InvestigationHistoryItem(BaseModel):
    id: str
    query: str
    agent_id: Optional[uuid.UUID] = None
    summary: str
    confidence_score: float
    investigated_at: datetime

    model_config = {"from_attributes": True}


class InvestigationHistoryResponse(BaseModel):
    items: list[InvestigationHistoryItem]
    total: int