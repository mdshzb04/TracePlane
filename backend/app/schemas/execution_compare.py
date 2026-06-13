import uuid
from typing import Optional

from pydantic import BaseModel, Field

from app.core.format import format_cost


class ExecutionCompareSide(BaseModel):
    execution_id: uuid.UUID
    agent_name: Optional[str] = None
    model: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None
    latency_ms: Optional[int] = None
    total_tokens: int = 0
    estimated_cost: Optional[float] = None
    status: str


class ExecutionCompareDiff(BaseModel):
    execution_a: ExecutionCompareSide
    execution_b: ExecutionCompareSide
    output_diff: Optional[str] = None
    prompt_diff: Optional[str] = None
    model_changed: bool = False
    latency_delta_ms: int = 0
    token_delta: int = 0
    cost_delta: float = 0.0
    status_changed: bool = False

    @property
    def cost_delta_formatted(self) -> float:
        return format_cost(self.cost_delta)
