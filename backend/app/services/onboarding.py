"""Workspace onboarding status for telemetry-first setup."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.api_key import ApiKey
from app.models.execution import Execution
from app.models.trace_span import TraceSpan
from app.models.user import User
from app.schemas.onboarding import OnboardingStatusResponse, OnboardingStep, WorkspaceUsage
from app.services.api_key_service import ApiKeyService


class OnboardingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_status(self, user: User) -> OnboardingStatusResponse:
        workspace_id = await ApiKeyService(self.session).ensure_user_workspace(user)

        api_key_count, agent_count, exec_result, span_count = await asyncio.gather(
            self._api_key_count(workspace_id),
            self._agent_count(workspace_id),
            self._execution_stats(workspace_id),
            self._span_count(workspace_id),
        )
        execution_count, usage = exec_result

        has_api_key = api_key_count > 0
        has_first_trace = execution_count > 0
        has_agent = agent_count > 0
        onboarding_complete = has_first_trace

        steps = [
            OnboardingStep(id="api_key", label="API Key Created", complete=has_api_key),
            OnboardingStep(id="sdk_installed", label="SDK Installed", complete=has_api_key),
            OnboardingStep(id="first_trace", label="First Trace Received", complete=has_first_trace),
            OnboardingStep(id="agent_discovered", label="Agent Auto-Discovered", complete=has_agent),
            OnboardingStep(id="dashboard_active", label="Dashboard Active", complete=has_first_trace),
        ]

        return OnboardingStatusResponse(
            has_api_key=has_api_key,
            has_first_trace=has_first_trace,
            has_agent=has_agent,
            onboarding_complete=onboarding_complete,
            execution_count=execution_count,
            span_count=span_count,
            agent_count=agent_count,
            steps=steps,
            usage=usage,
        )

    async def _count(self, stmt) -> int:
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def _api_key_count(self, workspace_id: uuid.UUID) -> int:
        return await self._count(
            select(func.count()).select_from(ApiKey).where(
                ApiKey.workspace_id == workspace_id,
                ApiKey.is_active == True,  # noqa: E712
            )
        )

    async def _agent_count(self, workspace_id: uuid.UUID) -> int:
        return await self._count(
            select(func.count()).select_from(Agent).where(Agent.workspace_id == workspace_id)
        )

    @staticmethod
    def _token_total_expr():
        return func.coalesce(
            cast(Execution.token_usage["total_tokens"].astext, Integer),
            func.coalesce(
                cast(Execution.token_usage["input_tokens"].astext, Integer),
                0,
            )
            + func.coalesce(
                cast(Execution.token_usage["output_tokens"].astext, Integer),
                0,
            ),
            0,
        )

    async def _execution_stats(self, workspace_id: uuid.UUID) -> tuple[int, WorkspaceUsage]:
        token_total = self._token_total_expr()
        stmt = (
            select(
                func.count(Execution.id),
                func.coalesce(func.sum(Execution.estimated_cost), 0),
                func.count().filter(Execution.status == "success"),
                func.coalesce(func.sum(token_total), 0),
            )
            .select_from(Execution)
            .join(Agent, Execution.agent_id == Agent.id)
            .where(Agent.workspace_id == workspace_id)
        )
        row = (await self.session.execute(stmt)).one()
        total = int(row[0] or 0)
        total_cost = float(row[1] or 0)
        success_count = int(row[2] or 0)
        total_tokens = int(row[3] or 0)
        success_rate = round((success_count / total) * 100, 1) if total else 0.0

        key_stmt = select(func.coalesce(func.sum(ApiKey.request_count), 0)).where(
            ApiKey.workspace_id == workspace_id
        )
        total_requests = int((await self.session.execute(key_stmt)).scalar() or 0)

        active_agents = await self._count(
            select(func.count()).select_from(Agent).where(
                Agent.workspace_id == workspace_id,
                Agent.status == "active",
            )
        )

        return total, WorkspaceUsage(
            total_requests=total_requests,
            total_tokens=total_tokens,
            total_cost=round(total_cost, 6),
            active_agents=active_agents,
            success_rate=success_rate,
        )

    async def _span_count(self, workspace_id: uuid.UUID) -> int:
        stmt = (
            select(func.count(TraceSpan.id))
            .select_from(TraceSpan)
            .join(Execution, TraceSpan.execution_id == Execution.id)
            .join(Agent, Execution.agent_id == Agent.id)
            .where(Agent.workspace_id == workspace_id)
        )
        return await self._count(stmt)
