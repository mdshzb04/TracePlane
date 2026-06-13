import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DatasetItem(BaseModel):
    test_case: str = Field(min_length=1)
    expected_output: Optional[str] = None


class EvaluationDatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    items: list[DatasetItem] = Field(default_factory=list)


class EvaluationDatasetRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: Optional[str] = None
    items: list[dict[str, Any]]
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvaluationRunCreate(BaseModel):
    dataset_id: uuid.UUID
    agent_id: uuid.UUID


class EvaluationRunResult(BaseModel):
    test_case: str
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    score: float
    evaluation_id: Optional[str] = None


class EvaluationRunRead(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    agent_id: uuid.UUID
    status: str
    average_score: Optional[float] = None
    results: list[EvaluationRunResult] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationScoreHistory(BaseModel):
    points: list[dict[str, Any]]
