import uuid

from fastapi import APIRouter, HTTPException

from app.core.dependencies import DbSession, DeveloperUser, ViewerUser
from app.core.workspace_scope import workspace_for_user
from app.schemas.provider import (
    ProviderCatalogItem,
    ProviderConnectRequest,
    ProviderConnectionRead,
    ProviderTestResult,
    ProviderTestTraceRequest,
)
from app.schemas.quickstart import QuickstartTestResponse
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderCatalogItem])
async def list_providers(current_user: ViewerUser, db: DbSession):
    ws = await workspace_for_user(db, current_user)
    service = ProviderService(db)
    return await service.list_catalog(ws)


@router.post("/{provider_id}/connect", response_model=ProviderConnectionRead)
async def connect_provider(
    provider_id: str,
    data: ProviderConnectRequest,
    current_user: DeveloperUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = ProviderService(db)
    try:
        return await service.connect(ws, provider_id, data.api_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{provider_id}", status_code=204)
async def disconnect_provider(
    provider_id: str,
    current_user: DeveloperUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = ProviderService(db)
    await service.disconnect(ws, provider_id)


@router.post("/{provider_id}/test", response_model=ProviderTestResult)
async def test_provider(
    provider_id: str,
    current_user: DeveloperUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = ProviderService(db)
    return await service.test(ws, provider_id)


@router.post("/{provider_id}/test-trace", response_model=QuickstartTestResponse)
async def test_provider_trace(
    provider_id: str,
    data: ProviderTestTraceRequest,
    current_user: DeveloperUser,
    db: DbSession,
):
    """Run a real LLM call with the stored provider key and ingest telemetry."""
    ws = await workspace_for_user(db, current_user)
    service = ProviderService(db)
    try:
        return await service.send_test_trace(
            ws,
            provider_id,
            traceplane_api_key=data.traceplane_api_key,
            model=data.model,
            prompt=data.prompt,
            agent_name=data.agent_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
