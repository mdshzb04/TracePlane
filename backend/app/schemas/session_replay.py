from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SessionReplayStep(BaseModel):
    step_index: int
    step_type: Literal["span", "llm", "tool", "error", "execution"]
    name: str
    status: str
    started_at: str
    ended_at: Optional[str] = None
    offset_ms: int = 0
    duration_ms: int = 0
    input_preview: Optional[str] = None
    output_preview: Optional[str] = None
    prompt: Optional[str] = None
    completion: Optional[str] = None
    tool_input: Optional[dict[str, Any]] = None
    tool_output: Optional[dict[str, Any]] = None
    token_usage: dict[str, Any] = Field(default_factory=dict)
    estimated_cost: Optional[float] = None
    error_message: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class SessionReplayResponse(BaseModel):
    execution_id: str
    total_duration_ms: int
    step_count: int
    error_count: int
    steps: list[SessionReplayStep]
