"""Workspace isolation — unit tests for scope helpers and repository filters."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.core.workspace_scope import get_agent_in_workspace, get_execution_in_workspace
from app.models.agent import Agent
from app.repositories.agent import AgentRepository


@pytest.mark.asyncio
async def test_get_agent_in_workspace_not_found():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)

    with pytest.raises(NotFoundError):
        await get_agent_in_workspace(session, uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_get_agent_in_workspace_found():
    agent_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    agent = Agent(name="A", owner="o", workspace_id=workspace_id)

    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = agent
    session.execute = AsyncMock(return_value=result)

    found = await get_agent_in_workspace(session, agent_id, workspace_id)
    assert found is agent


@pytest.mark.asyncio
async def test_get_execution_in_workspace_not_found():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)

    with pytest.raises(NotFoundError):
        await get_execution_in_workspace(session, uuid.uuid4(), uuid.uuid4())


def test_agent_search_includes_workspace_filter():
    """Repository must filter by workspace_id when provided."""
    repo = AgentRepository(session=MagicMock())  # type: ignore[arg-type]
    import inspect

    src = inspect.getsource(repo.search)
    assert "workspace_id" in src
    assert "Agent.workspace_id == workspace_id" in src
