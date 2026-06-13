import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.models.trace_span import TraceSpan
from app.schemas.ingest import IngestEvent, IngestSpan


def _event_span_type(event_type: str) -> str:
    et = event_type.lower()
    if et.startswith("model.") or et.startswith("llm.") or "completion" in et:
        return "llm"
    if et.startswith("tool.") or et.startswith("function."):
        return "tool"
    if et.startswith("error.") or "error" in et or et == "execution.failed":
        return "error"
    if et.startswith("execution."):
        return "root"
    return "custom"


def _span_name(event_type: str, event_data: dict[str, Any]) -> str:
    if event_data.get("name"):
        return str(event_data["name"])
    if event_data.get("tool"):
        return str(event_data["tool"])
    if event_data.get("model"):
        return str(event_data["model"])
    return event_type


class SpanBuilder:
    """Build hierarchical trace spans from SDK events or explicit span payloads."""

    def __init__(self, execution_id: uuid.UUID, base_time: Optional[datetime] = None):
        self.execution_id = execution_id
        self.base_time = base_time or datetime.now(timezone.utc)
        self._span_map: dict[str, uuid.UUID] = {}
        self._root_id: Optional[uuid.UUID] = None

    def from_explicit_spans(self, spans: list[IngestSpan]) -> list[TraceSpan]:
        created: list[TraceSpan] = []
        for item in spans:
            parent_id = None
            if item.parent_span_id and item.parent_span_id in self._span_map:
                parent_id = self._span_map[item.parent_span_id]
            elif item.parent_span_id and self._root_id:
                parent_id = self._root_id

            span = TraceSpan(
                execution_id=self.execution_id,
                parent_span_id=parent_id,
                external_span_id=item.span_id,
                name=item.name,
                span_type=item.span_type,
                status=item.status,
                started_at=item.started_at or self.base_time,
                ended_at=item.ended_at,
                latency_ms=item.latency_ms,
                attributes=item.attributes or {},
                token_usage=item.token_usage or {},
                estimated_cost=item.estimated_cost,
            )
            created.append(span)
            if item.span_id:
                self._span_map[item.span_id] = span.id
            if item.span_type == "root" and self._root_id is None:
                self._root_id = span.id
        return created

    def from_events(self, events: list[IngestEvent]) -> list[TraceSpan]:
        created: list[TraceSpan] = []
        root = TraceSpan(
            execution_id=self.execution_id,
            name="execution",
            span_type="root",
            status="success",
            started_at=self.base_time,
            attributes={},
        )
        created.append(root)
        self._root_id = root.id
        parent_id = root.id

        for event in events:
            event_data = event.event_data or {}
            span_type = _event_span_type(event.event_type)
            ts = event.timestamp or self.base_time
            latency = event_data.get("latency_ms")
            span = TraceSpan(
                execution_id=self.execution_id,
                parent_span_id=parent_id,
                name=_span_name(event.event_type, event_data),
                span_type=span_type,
                status="failed" if span_type == "error" else "success",
                started_at=ts,
                ended_at=ts,
                latency_ms=int(latency) if latency is not None else None,
                attributes={"event_type": event.event_type, **event_data},
                token_usage={
                    k: int(event_data[k])
                    for k in ("input_tokens", "output_tokens", "cached_tokens", "total_tokens")
                    if k in event_data and event_data[k] is not None
                },
                estimated_cost=event_data.get("cost") or event_data.get("estimated_cost"),
            )
            created.append(span)
        return created

    def default_root(self, agent_name: str, model: Optional[str]) -> TraceSpan:
        return TraceSpan(
            execution_id=self.execution_id,
            name=agent_name,
            span_type="root",
            status="success",
            started_at=self.base_time,
            attributes={"agent": agent_name, "model": model or ""},
        )
