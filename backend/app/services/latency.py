"""Resolve execution latency from ingest payloads and trace spans."""

from __future__ import annotations

from datetime import datetime

from app.models.trace_span import TraceSpan
from app.schemas.ingest import IngestTraceRequest


def resolve_execution_latency_ms(
    data: IngestTraceRequest,
    spans: list[TraceSpan],
) -> int | None:
    """Pick the best available latency measurement for an execution."""
    candidates: list[int] = []

    if data.latency_ms is not None and data.latency_ms > 0:
        candidates.append(int(data.latency_ms))

    for span in spans:
        if span.latency_ms is not None and span.latency_ms > 0:
            candidates.append(int(span.latency_ms))
            continue
        if span.started_at and span.ended_at:
            ms = _duration_ms(span.started_at, span.ended_at)
            if ms > 0:
                candidates.append(ms)

    for event in data.events or []:
        event_data = event.event_data or {}
        latency = event_data.get("latency_ms")
        if latency is not None:
            value = int(latency)
            if value > 0:
                candidates.append(value)

    if candidates:
        return max(candidates)
    return None


def _duration_ms(started_at: datetime, ended_at: datetime) -> int:
    return max(0, int((ended_at - started_at).total_seconds() * 1000))
