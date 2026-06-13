"""Execution replay — re-run historical executions and compare results."""

from __future__ import annotations

import difflib
import logging
import time
import uuid
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.format import format_cost
from app.llm import get_llm_provider
from app.llm.pricing import estimate_cost
from app.models.execution import Execution
from app.models.execution_event import ExecutionEvent
from app.repositories.execution import ExecutionRepository
from app.repositories.execution_event import ExecutionEventRepository
from app.schemas.execution import ReplayDiff, ReplayMetrics, ReplayResponse

logger = logging.getLogger(__name__)


def _total_tokens(token_usage: dict | None) -> int:
    if not token_usage:
        return 0
    if token_usage.get("total_tokens"):
        return int(token_usage["total_tokens"])
    return int(token_usage.get("input_tokens", 0) or 0) + int(token_usage.get("output_tokens", 0) or 0)


def _build_diff(original: Execution, replay: Execution) -> ReplayDiff:
    orig_tokens = _total_tokens(original.token_usage)
    replay_tokens = _total_tokens(replay.token_usage)
    orig_cost = float(original.estimated_cost or 0)
    replay_cost = float(replay.estimated_cost or 0)
    orig_latency = original.latency_ms or 0
    replay_latency = replay.latency_ms or 0

    output_changed = (original.output or "") != (replay.output or "")
    output_diff = None
    if output_changed:
        output_diff = "\n".join(
            difflib.unified_diff(
                (original.output or "").splitlines(),
                (replay.output or "").splitlines(),
                fromfile="original",
                tofile="replay",
                lineterm="",
            )
        )

    latency_increased = replay_latency > orig_latency * 1.1 and replay_latency - orig_latency > 50
    tokens_increased = replay_tokens > orig_tokens * 1.1 and replay_tokens - orig_tokens > 10
    cost_increased = replay_cost > orig_cost * 1.1 and replay_cost - orig_cost > 0.000001
    quality_dropped = original.status == "success" and replay.status == "failed"
    if output_changed and original.status == "success" and replay.status == "success":
        quality_dropped = len(replay.output or "") < len(original.output or "") * 0.5

    warnings: list[str] = []
    if quality_dropped:
        warnings.append("Replay output quality may have degraded vs the original run")
    if latency_increased:
        warnings.append(f"Latency increased by {replay_latency - orig_latency}ms")
    if tokens_increased:
        warnings.append(f"Token usage increased by {replay_tokens - orig_tokens}")
    if cost_increased:
        warnings.append("Replay cost is higher than the original execution")
    if output_changed and not quality_dropped:
        warnings.append("Replay output differs from the original response")

    return ReplayDiff(
        original=ReplayMetrics(
            execution_id=original.id,
            output=original.output,
            latency_ms=original.latency_ms,
            total_tokens=orig_tokens,
            estimated_cost=format_cost(orig_cost),
            status=original.status,
        ),
        replay=ReplayMetrics(
            execution_id=replay.id,
            output=replay.output,
            latency_ms=replay.latency_ms,
            total_tokens=replay_tokens,
            estimated_cost=format_cost(replay_cost),
            status=replay.status,
        ),
        output_changed=output_changed,
        output_diff=output_diff,
        latency_increased=latency_increased,
        tokens_increased=tokens_increased,
        cost_increased=cost_increased,
        quality_dropped=quality_dropped,
        regression_warnings=warnings,
    )


class ReplayService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.exec_repo = ExecutionRepository(session)
        self.event_repo = ExecutionEventRepository(session)

    async def replay(self, execution_id: uuid.UUID, workspace_id: uuid.UUID) -> ReplayResponse:
        from app.core.workspace_scope import get_execution_in_workspace

        original = await get_execution_in_workspace(self.session, execution_id, workspace_id)

        now = datetime.now(timezone.utc)
        replay_exec = Execution(
            agent_id=original.agent_id,
            input=original.input,
            model=original.model,
            status="running",
            token_usage={},
            estimated_cost=0,
            started_at=now,
            replay_of_id=original.id,
            is_replay=True,
        )
        replay_exec = await self.exec_repo.create(replay_exec)
        await self.session.flush()

        start = time.perf_counter()
        output: str | None = None
        status = "success"
        token_usage: dict = {}
        cost = 0.0

        provider = get_llm_provider()
        if provider.is_configured() and original.input:
            try:
                response = await provider.invoke(
                    [
                        SystemMessage(content="Replay the following agent request faithfully."),
                        HumanMessage(content=original.input),
                    ]
                )
                output = response.content
                token_usage = {
                    "input_tokens": getattr(response, "usage_metadata", {}) or {},
                }
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    um = response.usage_metadata
                    token_usage = {
                        "input_tokens": um.get("input_tokens", 0),
                        "output_tokens": um.get("output_tokens", 0),
                        "total_tokens": um.get("total_tokens", 0),
                    }
                else:
                    token_usage = {"input_tokens": 0, "output_tokens": len(output or "") // 4, "total_tokens": len(output or "") // 4}
                cost = estimate_cost(original.model or "gpt-4o-mini", token_usage.get("input_tokens", 0), token_usage.get("output_tokens", 0)) or 0
            except Exception as exc:
                logger.warning("Replay LLM failed: %s", exc)
                status = "failed"
                output = str(exc)
        else:
            raise BadRequestError(
                "Replay requires a configured LLM provider. Set OPENAI_API_KEY or NVIDIA_API_KEY."
            )

        latency_ms = int((time.perf_counter() - start) * 1000)

        replay_exec.output = output
        replay_exec.status = status
        replay_exec.latency_ms = latency_ms
        replay_exec.token_usage = token_usage
        replay_exec.estimated_cost = cost
        replay_exec.completed_at = datetime.now(timezone.utc)
        await self.session.flush()

        await self.event_repo.create(
            ExecutionEvent(
                execution_id=replay_exec.id,
                event_type="execution.replayed",
                event_data={"original_execution_id": str(original.id), "model": original.model},
            )
        )
        await self.session.flush()

        diff = _build_diff(original, replay_exec)
        logger.info("Replay complete: original=%s replay=%s", original.id, replay_exec.id)
        return ReplayResponse(replay_execution_id=replay_exec.id, diff=diff, replay_mode="llm")
