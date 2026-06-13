from fastapi import APIRouter, HTTPException

from app.core.dependencies import DbSession, DeveloperUser
from app.core.workspace_scope import workspace_for_user
from app.schemas.quickstart import QuickstartTestRequest, QuickstartTestResponse
from app.services.quickstart_service import QuickstartService

router = APIRouter(prefix="/quickstart", tags=["quickstart"])


@router.post("/test-request", response_model=QuickstartTestResponse)
async def send_test_request(
    data: QuickstartTestRequest,
    current_user: DeveloperUser,
    db: DbSession,
):
    """Run a real provider LLM call and ingest telemetry for the quickstart flow."""
    ws = await workspace_for_user(db, current_user)
    service = QuickstartService(db)
    try:
        return await service.send_test_request(
            workspace_id=ws,
            provider_id=data.provider_id,
            provider_api_key=data.provider_api_key,
            traceplane_api_key=data.traceplane_api_key,
            model=data.model,
            prompt=data.prompt,
            agent_name=data.agent_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
