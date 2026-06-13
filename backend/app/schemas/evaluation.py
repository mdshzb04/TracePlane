import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EvaluationCreate(BaseModel):
    agent_id: uuid.UUID
    test_case: str = Field(min_length=1)
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)


class EvaluationRead(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    test_case: str
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    score: Optional[float] = None
    evaluation_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvaluationListParams(BaseModel):
    agent_id: Optional[uuid.UUID] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedEvaluationResponse(BaseModel):
    items: list[EvaluationRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class BenchmarkCaseInput(BaseModel):
    test_case: str = Field(min_length=1)
    expected_output: Optional[str] = None


class BenchmarkRunRequest(BaseModel):
    test_cases: list[BenchmarkCaseInput] = Field(min_length=1, max_length=20)


class BenchmarkCaseResult(BaseModel):
    evaluation_id: uuid.UUID
    execution_id: uuid.UUID
    test_case: str
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    score: float
    status: str


class BenchmarkRunResponse(BaseModel):
    agent_id: uuid.UUID
    results: list[BenchmarkCaseResult]
    average_score: float