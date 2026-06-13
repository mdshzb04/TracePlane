from pydantic import BaseModel, Field


class OnboardingStep(BaseModel):
    id: str
    label: str
    complete: bool


class WorkspaceUsage(BaseModel):
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    active_agents: int = 0
    success_rate: float = 0.0


class OnboardingStatusResponse(BaseModel):
    has_api_key: bool
    has_first_trace: bool
    has_agent: bool
    onboarding_complete: bool
    execution_count: int = 0
    span_count: int = 0
    agent_count: int = 0
    steps: list[OnboardingStep] = Field(default_factory=list)
    usage: WorkspaceUsage = Field(default_factory=WorkspaceUsage)
