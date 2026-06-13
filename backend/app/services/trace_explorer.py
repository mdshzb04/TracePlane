import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trace_span import TraceSpan
from app.schemas.analytics import TraceEvent, TraceSpanNode, TraceTimelines


def _classify_event(event_type: str) -> str:
    et = event_type.lower()
    if et.startswith("model.") or et.startswith("llm.") or "completion" in et:
        return "llm"
    if et.startswith("tool.") or et.startswith("function."):
        return "tool"
    if et.startswith("error.") or "error" in et or et == "execution.failed":
        return "error"
    return "other"


def build_span_tree(spans: list[TraceSpan]) -> list[TraceSpanNode]:
    nodes: dict[str, TraceSpanNode] = {}
    for span in spans:
        nodes[str(span.id)] = TraceSpanNode(
            id=str(span.id),
            parent_span_id=str(span.parent_span_id) if span.parent_span_id else None,
            name=span.name,
            span_type=span.span_type,
            status=span.status,
            started_at=span.started_at.isoformat() if span.started_at else "",
            ended_at=span.ended_at.isoformat() if span.ended_at else None,
            latency_ms=span.latency_ms,
            attributes=span.attributes or {},
            token_usage=span.token_usage or {},
            estimated_cost=float(span.estimated_cost) if span.estimated_cost else None,
            children=[],
        )

    roots: list[TraceSpanNode] = []
    for span in spans:
        node = nodes[str(span.id)]
        if span.parent_span_id and str(span.parent_span_id) in nodes:
            nodes[str(span.parent_span_id)].children.append(node)
        else:
            roots.append(node)
    return roots


def build_timelines(events: list[TraceEvent]) -> TraceTimelines:
    llm: list[TraceEvent] = []
    tools: list[TraceEvent] = []
    errors: list[TraceEvent] = []
    for event in events:
        kind = _classify_event(event.event_type)
        if kind == "llm":
            llm.append(event)
        elif kind == "tool":
            tools.append(event)
        elif kind == "error":
            errors.append(event)
    return TraceTimelines(llm_calls=llm, tool_calls=tools, errors=errors)


class TraceExplorerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_spans(self, execution_id: uuid.UUID) -> list[TraceSpan]:
        stmt = (
            select(TraceSpan)
            .where(TraceSpan.execution_id == execution_id)
            .order_by(TraceSpan.started_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_span_tree(self, execution_id: uuid.UUID) -> list[TraceSpanNode]:
        spans = await self.get_spans(execution_id)
        if not spans:
            return []
        return build_span_tree(spans)
