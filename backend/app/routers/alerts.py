import uuid

from fastapi import APIRouter, HTTPException

from app.core.dependencies import DbSession, DeveloperUser, ViewerUser
from app.core.workspace_scope import workspace_for_user
from app.schemas.alert import (
    AlertEvaluationResult,
    AlertEventRead,
    AlertRuleCreate,
    AlertRuleRead,
    AlertRuleUpdate,
    AlertTestEmailRequest,
    AlertTestEmailResponse,
)
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRuleRead])
async def list_alerts(current_user: ViewerUser, db: DbSession):
    ws = await workspace_for_user(db, current_user)
    service = AlertService(db)
    return await service.list_rules(ws)


@router.get("/events", response_model=list[AlertEventRead])
async def list_alert_events(
    current_user: ViewerUser,
    db: DbSession,
    rule_id: uuid.UUID | None = None,
    limit: int = 50,
):
    ws = await workspace_for_user(db, current_user)
    service = AlertService(db)
    return await service.list_events(ws, rule_id=rule_id, limit=limit)


@router.get("/{rule_id}/events", response_model=list[AlertEventRead])
async def list_rule_alert_events(
    rule_id: uuid.UUID,
    current_user: ViewerUser,
    db: DbSession,
    limit: int = 50,
):
    ws = await workspace_for_user(db, current_user)
    service = AlertService(db)
    return await service.list_events(ws, rule_id=rule_id, limit=limit)


@router.post("", response_model=AlertRuleRead, status_code=201)
async def create_alert(
    data: AlertRuleCreate,
    current_user: DeveloperUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = AlertService(db)
    return await service.create_rule(ws, data, current_user.id)


@router.post("/test-email", response_model=AlertTestEmailResponse)
async def send_test_email(
    data: AlertTestEmailRequest,
    current_user: DeveloperUser,
    db: DbSession,
):
    """Send a test email via Resend to verify alert delivery."""
    ws = await workspace_for_user(db, current_user)
    service = AlertService(db)
    try:
        result = await service.send_test_email(ws, data.recipient)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error or result.message)
    return result


@router.put("/{rule_id}", response_model=AlertRuleRead)
async def update_alert(
    rule_id: uuid.UUID,
    data: AlertRuleUpdate,
    current_user: DeveloperUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = AlertService(db)
    try:
        return await service.update_rule(ws, rule_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{rule_id}", status_code=204)
async def delete_alert(
    rule_id: uuid.UUID,
    current_user: DeveloperUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = AlertService(db)
    try:
        await service.delete_rule(ws, rule_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{rule_id}/evaluate", response_model=AlertEvaluationResult)
async def evaluate_alert(
    rule_id: uuid.UUID,
    current_user: DeveloperUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = AlertService(db)
    try:
        return await service.evaluate_rule(ws, rule_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/evaluate-all", response_model=list[AlertEvaluationResult])
async def evaluate_all_alerts(current_user: DeveloperUser, db: DbSession):
    ws = await workspace_for_user(db, current_user)
    service = AlertService(db)
    return await service.evaluate_all(ws)
