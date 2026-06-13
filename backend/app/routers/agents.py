import math
import uuid
from typing import Optional

from fastapi import APIRouter, Query

from app.core.dependencies import AdminUser, CurrentUser, DbSession, DeveloperUser, ViewerUser
from app.core.workspace_scope import workspace_for_user
from app.schemas.agent import AgentDetailRead, AgentListParams, AgentRead, AgentUpdate, PaginatedAgentResponse
from app.services.agent import AgentService
from app.services.agent_observability import AgentObservabilityService
from app.services.audit import AuditService

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=PaginatedAgentResponse)
async def list_agents(
    current_user: ViewerUser,
    db: DbSession,
    status: Optional[str] = Query(default=None),
    owner: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=200),
    tags: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    ws = await workspace_for_user(db, current_user)
    tag_list = tags.split(",") if tags else None
    params = AgentListParams(
        status=status, owner=owner, search=search, tags=tag_list, page=page, page_size=page_size
    )
    service = AgentService(db)
    items, total = await service.list_agents(params, workspace_id=ws)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedAgentResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/{agent_id}/detail", response_model=AgentDetailRead)
async def get_agent_detail(
    agent_id: uuid.UUID,
    current_user: ViewerUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = AgentObservabilityService(db)
    return await service.get_agent_detail(agent_id, workspace_id=ws)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: uuid.UUID,
    current_user: ViewerUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = AgentService(db)
    return await service.get_agent(agent_id, workspace_id=ws)


@router.put("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: uuid.UUID,
    data: AgentUpdate,
    current_user: DeveloperUser,
    db: DbSession,
):
    ws = await workspace_for_user(db, current_user)
    service = AgentService(db)
    audit = AuditService(db)
    agent = await service.update_agent(agent_id, data, workspace_id=ws)
    await audit.log(
        action="agent.update",
        resource_type="agent",
        resource_id=agent.id,
        user_id=current_user.id,
        details=data.model_dump(exclude_unset=True),
    )
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    from app.auth.roles import Role
    from app.core.exceptions import ForbiddenError

    if current_user.role != Role.ADMIN.value:
        raise ForbiddenError("Only admins can delete agents")
    ws = await workspace_for_user(db, current_user)
    service = AgentService(db)
    audit = AuditService(db)
    await service.delete_agent(agent_id, workspace_id=ws)
    await audit.log(
        action="agent.delete",
        resource_type="agent",
        resource_id=agent_id,
        user_id=current_user.id,
    )
