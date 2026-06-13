import math
import uuid
from typing import Optional

from fastapi import APIRouter, Query

from app.core.dependencies import DbSession, DeveloperUser, ViewerUser
from app.core.workspace_scope import workspace_for_user
from app.schemas.execution import (
    ExecutionCreate,
    ExecutionDetailRead,
    ExecutionEventCreate,
    ExecutionEventRead,
    ExecutionListParams,
    ExecutionRead,
    ExecutionUpdate,
    PaginatedExecutionResponse,
    ReplayResponse,
)
from app.schemas.execution_compare import ExecutionCompareDiff
from app.schemas.session_replay import SessionReplayResponse
from app.services.execution import ExecutionService
from app.services.execution_compare import ExecutionCompareService
from app.services.replay import ReplayService
from app.services.session_replay import SessionReplayService

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=PaginatedExecutionResponse)
async def list_executions(
    current_user: ViewerUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
    status: Optional[str] = Query(default=None),
    model: Optional[str] = Query(default=None),
    provider: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=200),
    sort_by: str = Query(default="started_at"),
    sort_order: str = Query(default="desc"),
    min_cost: Optional[float] = Query(default=None, ge=0),
    max_cost: Optional[float] = Query(default=None, ge=0),
    min_latency: Optional[int] = Query(default=None, ge=0),
    max_latency: Optional[int] = Query(default=None, ge=0),
    min_tokens: Optional[int] = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    params = ExecutionListParams(
        agent_id=agent_id,
        status=status,
        model=model,
        provider=provider,
        search=search,
        sort_by=sort_by,  # type: ignore[arg-type]
        sort_order=sort_order,  # type: ignore[arg-type]
        min_cost=min_cost,
        max_cost=max_cost,
        min_latency=min_latency,
        max_latency=max_latency,
        min_tokens=min_tokens,
        page=page,
        page_size=page_size,
    )
    ws = await workspace_for_user(db, current_user)
    service = ExecutionService(db)
    items, total, summary = await service.list_executions(params, workspace_id=ws)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedExecutionResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        summary=summary,
    )


@router.post("", response_model=ExecutionRead, status_code=201)
async def create_execution(
    data: ExecutionCreate,
    current_user: DeveloperUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = ExecutionService(db)
    return await service.create_execution(data, workspace_id=ws, user_id=str(current_user.id))


@router.get("/compare", response_model=ExecutionCompareDiff)
async def compare_executions(
    current_user: ViewerUser,
    db: DbSession,
    execution_a: uuid.UUID = Query(...),
    execution_b: uuid.UUID = Query(...),
):
    ws = await workspace_for_user(db, current_user)
    service = ExecutionCompareService(db)
    return await service.compare(execution_a, execution_b, workspace_id=ws)


@router.get("/{execution_id}", response_model=ExecutionRead)
async def get_execution(
    execution_id: uuid.UUID,
    current_user: ViewerUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = ExecutionService(db)
    return await service.get_execution(execution_id, workspace_id=ws)


@router.get("/{execution_id}/detail", response_model=ExecutionDetailRead)
async def get_execution_detail(
    execution_id: uuid.UUID,
    current_user: ViewerUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = ExecutionService(db)
    return await service.get_execution_detail(execution_id, workspace_id=ws)


@router.get("/{execution_id}/session-replay", response_model=SessionReplayResponse)
async def session_replay(
    execution_id: uuid.UUID,
    current_user: ViewerUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = SessionReplayService(db)
    return await service.build_replay(execution_id, workspace_id=ws)


@router.post("/{execution_id}/replay", response_model=ReplayResponse)
async def replay_execution(
    execution_id: uuid.UUID,
    current_user: DeveloperUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = ReplayService(db)
    return await service.replay(execution_id, workspace_id=ws)


@router.put("/{execution_id}", response_model=ExecutionRead)
async def update_execution(
    execution_id: uuid.UUID,
    data: ExecutionUpdate,
    current_user: DeveloperUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = ExecutionService(db)
    return await service.update_execution(execution_id, data, workspace_id=ws)


@router.post("/{execution_id}/events", response_model=ExecutionEventRead, status_code=201)
async def add_execution_event(
    execution_id: uuid.UUID,
    data: ExecutionEventCreate,
    current_user: DeveloperUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = ExecutionService(db)
    return await service.add_event(execution_id, data, workspace_id=ws)


@router.get("/{execution_id}/events", response_model=list[ExecutionEventRead])
async def get_execution_events(
    execution_id: uuid.UUID,
    current_user: ViewerUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = ExecutionService(db)
    return await service.get_events(execution_id, workspace_id=ws)
