"""Session replay — step-by-step waterfall from stored spans and events."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.execution import ExecutionRepository
from app.repositories.execution_event import ExecutionEventRepository
from app.schemas.session_replay import SessionReplayResponse, SessionReplayStep
from app.services.trace_explorer import TraceExplorerService


def _parse_ts(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _preview(text: str | None, limit: int = 400) -> str | None:
    if not text:
        return None
    return text if len(text) <= limit else text[:limit] + "…"


class SessionReplayService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.exec_repo = ExecutionRepository(session)
        self.event_repo = ExecutionEventRepository(session)
        self.trace = TraceExplorerService(session)

    async def build_replay(
        self, execution_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> SessionReplayResponse:
        from app.core.workspace_scope import get_execution_in_workspace

        execution = await get_execution_in_workspace(self.session, execution_id, workspace_id)

        spans = await self.trace.get_spans(execution_id)
        events = await self.event_repo.get_by_execution_id(execution_id, limit=500)

        origin = execution.started_at
        steps: list[SessionReplayStep] = []
        error_count = 0

        if execution.input or execution.output:
            steps.append(
                SessionReplayStep(
                    step_index=0,
                    step_type="execution",
                    name="execution.root",
                    status=execution.status,
                    started_at=execution.started_at.isoformat(),
                    ended_at=execution.completed_at.isoformat() if execution.completed_at else None,
                    offset_ms=0,
                    duration_ms=execution.latency_ms or 0,
                    input_preview=_preview(execution.input),
                    output_preview=_preview(execution.output),
                    prompt=_preview(execution.input, 2000),
                    completion=_preview(execution.output, 2000),
                    token_usage=execution.token_usage or {},
                    estimated_cost=float(execution.estimated_cost or 0),
                )
            )

        for idx, span in enumerate(spans):
            started = span.started_at or origin
            offset = int((started - origin).total_seconds() * 1000) if started and origin else 0
            attrs = span.attributes or {}
            step_type = span.span_type if span.span_type in ("llm", "tool", "error") else "span"
            if step_type == "error":
                error_count += 1

            steps.append(
                SessionReplayStep(
                    step_index=len(steps),
                    step_type=step_type,  # type: ignore[arg-type]
                    name=span.name,
                    status=span.status,
                    started_at=started.isoformat() if started else "",
                    ended_at=span.ended_at.isoformat() if span.ended_at else None,
                    offset_ms=max(0, offset),
                    duration_ms=span.latency_ms or 0,
                    input_preview=_preview(attrs.get("input") or attrs.get("prompt")),
                    output_preview=_preview(attrs.get("output") or attrs.get("completion")),
                    prompt=_preview(attrs.get("prompt") or attrs.get("input"), 2000),
                    completion=_preview(attrs.get("completion") or attrs.get("output"), 2000),
                    tool_input=attrs.get("tool_input") if isinstance(attrs.get("tool_input"), dict) else None,
                    tool_output=attrs.get("tool_output") if isinstance(attrs.get("tool_output"), dict) else None,
                    token_usage=span.token_usage or {},
                    estimated_cost=float(span.estimated_cost) if span.estimated_cost else None,
                    error_message=attrs.get("error") or attrs.get("message"),
                    attributes=attrs,
                )
            )

        for event in events:
            et = event.event_type.lower()
            if et.startswith("error.") or "failed" in et:
                error_count += 1
            kind = "llm" if "llm" in et or "model" in et else "tool" if "tool" in et else "error" if "error" in et else "span"
            data = event.event_data or {}
            ts = event.timestamp or origin
            offset = int((ts - origin).total_seconds() * 1000) if ts and origin else 0
            steps.append(
                SessionReplayStep(
                    step_index=len(steps),
                    step_type=kind,  # type: ignore[arg-type]
                    name=event.event_type,
                    status="failed" if kind == "error" else "success",
                    started_at=ts.isoformat() if ts else "",
                    offset_ms=max(0, offset),
                    duration_ms=int(data.get("latency_ms") or data.get("duration_ms") or 0),
                    prompt=_preview(data.get("prompt") or data.get("input"), 2000),
                    completion=_preview(data.get("completion") or data.get("output"), 2000),
                    tool_input=data.get("input") if isinstance(data.get("input"), dict) else None,
                    tool_output=data.get("output") if isinstance(data.get("output"), dict) else None,
                    token_usage={
                        k: data[k]
                        for k in ("input_tokens", "output_tokens", "total_tokens")
                        if k in data
                    },
                    estimated_cost=float(data["cost"]) if data.get("cost") is not None else None,
                    error_message=data.get("error") or data.get("message"),
                    attributes=data,
                )
            )

        steps.sort(key=lambda s: (s.offset_ms, s.step_index))
        for i, step in enumerate(steps):
            step.step_index = i

        total_duration = execution.latency_ms or 0
        if steps:
            total_duration = max(total_duration, max(s.offset_ms + s.duration_ms for s in steps))

        return SessionReplayResponse(
            execution_id=str(execution_id),
            total_duration_ms=total_duration,
            step_count=len(steps),
            error_count=error_count,
            steps=steps,
        )
