from app.schemas.onboarding import OnboardingStatusResponse, OnboardingStep, WorkspaceUsage


def test_onboarding_incomplete_defaults():
    status = OnboardingStatusResponse(
        has_api_key=False,
        has_first_trace=False,
        has_agent=False,
        onboarding_complete=False,
    )
    assert status.execution_count == 0
    assert status.steps == []
    assert status.usage.total_requests == 0


def test_onboarding_complete_with_steps():
    status = OnboardingStatusResponse(
        has_api_key=True,
        has_first_trace=True,
        has_agent=True,
        onboarding_complete=True,
        execution_count=12,
        steps=[
            OnboardingStep(id="api_key", label="Create API key", complete=True),
            OnboardingStep(id="first_trace", label="Send first trace", complete=True),
        ],
        usage=WorkspaceUsage(total_requests=12, total_tokens=4000, total_cost=0.42, active_agents=2, success_rate=91.0),
    )
    assert status.onboarding_complete
    assert len(status.steps) == 2
    assert status.usage.success_rate == 91.0
