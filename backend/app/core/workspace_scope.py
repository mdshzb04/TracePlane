"""Workspace isolation helpers for multi-tenant resource access."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.agent import Agent
from app.models.execution import Execution
from app.models.user import User
from app.core.cache import get_cached, set_cached
from app.services.api_key_service import ApiKeyService


async def workspace_for_user(session: AsyncSession, user: User) -> uuid.UUID:
    if user.workspace_id:
        return user.workspace_id

    key = f"workspace:{user.id}"
    cached = get_cached(key)
    if cached is not None:
        return uuid.UUID(str(cached))

    workspace_id = await ApiKeyService(session).ensure_user_workspace(user)
    set_cached(key, str(workspace_id), 300)
    return workspace_id


async def get_agent_in_workspace(
    session: AsyncSession, agent_id: uuid.UUID, workspace_id: uuid.UUID
) -> Agent:
    agent = (
        await session.execute(
            select(Agent).where(Agent.id == agent_id, Agent.workspace_id == workspace_id)
        )
    ).scalar_one_or_none()
    if agent is None:
        raise NotFoundError("Agent", str(agent_id))
    return agent


async def get_execution_in_workspace(
    session: AsyncSession, execution_id: uuid.UUID, workspace_id: uuid.UUID
) -> Execution:
    execution = (
        await session.execute(
            select(Execution)
            .join(Agent, Agent.id == Execution.agent_id)
            .where(Execution.id == execution_id, Agent.workspace_id == workspace_id)
        )
    ).scalar_one_or_none()
    if execution is None:
        raise NotFoundError("Execution", str(execution_id))
    return execution
