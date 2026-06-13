import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.workspace_scope import get_agent_in_workspace
from app.models.agent import Agent
from app.repositories.agent import AgentRepository
from app.schemas.agent import AgentCreate, AgentListParams, AgentRead, AgentUpdate

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.agent_repo = AgentRepository(session)

    async def create_agent(self, data: AgentCreate, created_by: uuid.UUID) -> AgentRead:
        workflow = [n.model_dump() for n in data.workflow] if data.workflow else []
        agent = Agent(
            name=data.name,
            description=data.description,
            owner=data.owner,
            model=data.model,
            tags=data.tags or [],
            workflow=workflow,
            tools=data.tools or [],
            status="active",
            created_by=created_by,
        )
        agent = await self.agent_repo.create(agent)
        await self.session.flush()
        logger.info("Agent created: %s (%s)", agent.name, agent.id)
        return AgentRead.model_validate(agent)

    async def get_agent(self, agent_id: uuid.UUID, workspace_id: uuid.UUID) -> AgentRead:
        agent = await get_agent_in_workspace(self.session, agent_id, workspace_id)
        return AgentRead.model_validate(agent)

    async def list_agents(
        self, params: AgentListParams, workspace_id: uuid.UUID
    ) -> tuple[list[AgentRead], int]:
        offset = (params.page - 1) * params.page_size
        items, total = await self.agent_repo.search(
            workspace_id=workspace_id,
            status=params.status,
            owner=params.owner,
            search=params.search,
            tags=params.tags,
            offset=offset,
            limit=params.page_size,
        )
        return [AgentRead.model_validate(a) for a in items], total

    async def update_agent(
        self, agent_id: uuid.UUID, data: AgentUpdate, workspace_id: uuid.UUID
    ) -> AgentRead:
        agent = await get_agent_in_workspace(self.session, agent_id, workspace_id)

        updates = data.model_dump(exclude_unset=True)
        if "tags" in updates and updates["tags"] is not None:
            updates["tags"] = list(updates["tags"]) if updates["tags"] else []

        agent = await self.agent_repo.update(agent, updates)
        logger.info("Agent updated: %s (%s)", agent.name, agent.id)
        return AgentRead.model_validate(agent)

    async def delete_agent(self, agent_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
        agent = await get_agent_in_workspace(self.session, agent_id, workspace_id)
        await self.agent_repo.delete(agent)
        logger.info("Agent deleted: %s (%s)", agent.name, agent.id)