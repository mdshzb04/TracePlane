from datetime import datetime, timezone

from app.models.trace_span import TraceSpan
from app.schemas.ingest import IngestAgentMeta, IngestEvent, IngestTraceRequest
from app.services.latency import resolve_execution_latency_ms


def test_prefers_positive_execution_latency():
    data = IngestTraceRequest(agent=IngestAgentMeta(name="bot"), latency_ms=1200)
    assert resolve_execution_latency_ms(data, []) == 1200


def test_falls_back_to_span_latency_when_execution_is_zero():
    data = IngestTraceRequest(agent=IngestAgentMeta(name="bot"), latency_ms=0)
    span = TraceSpan(
        execution_id=None,
        name="llm",
        span_type="llm",
        status="success",
        started_at=datetime.now(timezone.utc),
        latency_ms=842,
    )
    assert resolve_execution_latency_ms(data, [span]) == 842


def test_uses_event_latency_from_model_call():
    data = IngestTraceRequest(
        agent=IngestAgentMeta(name="bot"),
        events=[
            IngestEvent(
                event_type="model.call.completed",
                event_data={"model": "gpt-4o-mini", "latency_ms": 1534},
            )
        ],
    )
    assert resolve_execution_latency_ms(data, []) == 1534
