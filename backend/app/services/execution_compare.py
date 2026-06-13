"""Compare two executions — output, input, cost, token, latency, model diffs."""

from __future__ import annotations

import difflib
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.core.workspace_scope import get_execution_in_workspace
from app.core.format import format_cost
from app.repositories.agent import AgentRepository
from app.repositories.execution import ExecutionRepository
from app.schemas.execution_compare import ExecutionCompareDiff, ExecutionCompareSide


def _total_tokens(token_usage: dict | None) -> int:
    if not token_usage:
        return 0
    if token_usage.get("total_tokens"):
        return int(token_usage["total_tokens"])
    return int(token_usage.get("input_tokens", 0) or 0) + int(token_usage.get("output_tokens", 0) or 0)


class ExecutionCompareService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.exec_repo = ExecutionRepository(session)
        self.agent_repo = AgentRepository(session)

    async def compare(
        self, execution_a_id: uuid.UUID, execution_b_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> ExecutionCompareDiff:
        if execution_a_id == execution_b_id:
            raise BadRequestError("Cannot compare an execution with itself")

        a = await get_execution_in_workspace(self.session, execution_a_id, workspace_id)
        b = await get_execution_in_workspace(self.session, execution_b_id, workspace_id)

        side_a = await self._to_side(a)
        side_b = await self._to_side(b)

        output_diff = None
        if (a.output or "") != (b.output or ""):
            output_diff = "\n".join(
                difflib.unified_diff(
                    (a.output or "").splitlines(),
                    (b.output or "").splitlines(),
                    fromfile="execution_a",
                    tofile="execution_b",
                    lineterm="",
                )
            )

        prompt_diff = None
        if (a.input or "") != (b.input or ""):
            prompt_diff = "\n".join(
                difflib.unified_diff(
                    (a.input or "").splitlines(),
                    (b.input or "").splitlines(),
                    fromfile="prompt_a",
                    tofile="prompt_b",
                    lineterm="",
                )
            )

        cost_a = float(a.estimated_cost or 0)
        cost_b = float(b.estimated_cost or 0)

        return ExecutionCompareDiff(
            execution_a=side_a,
            execution_b=side_b,
            output_diff=output_diff,
            prompt_diff=prompt_diff,
            model_changed=(a.model or "") != (b.model or ""),
            latency_delta_ms=(b.latency_ms or 0) - (a.latency_ms or 0),
            token_delta=_total_tokens(b.token_usage) - _total_tokens(a.token_usage),
            cost_delta=format_cost(cost_b - cost_a),
            status_changed=a.status != b.status,
        )

    async def _to_side(self, execution) -> ExecutionCompareSide:
        agent = await self.agent_repo.get_by_id(execution.agent_id)
        return ExecutionCompareSide(
            execution_id=execution.id,
            agent_name=agent.name if agent else None,
            model=execution.model,
            input=execution.input,
            output=execution.output,
            latency_ms=execution.latency_ms,
            total_tokens=_total_tokens(execution.token_usage),
            estimated_cost=format_cost(execution.estimated_cost),
            status=execution.status,
        )
