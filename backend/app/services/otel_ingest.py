"""OpenTelemetry trace ingestion — map OTLP JSON to Traceplane ingest schema."""

from __future__ import annotations

from typing import Any

from app.schemas.ingest import IngestAgentMeta, IngestEvent, IngestSpan, IngestTraceRequest


def otel_resource_spans_to_ingest(payload: dict[str, Any], *, default_agent: str = "otel-agent") -> IngestTraceRequest:
    """Convert OTLP/JSON export (resourceSpans) into IngestTraceRequest."""
    resource_spans = payload.get("resourceSpans") or payload.get("resource_spans") or []
    if not resource_spans and "spans" in payload:
        resource_spans = [{"scopeSpans": [{"spans": payload["spans"]}]}]

    spans: list[IngestSpan] = []
    events: list[IngestEvent] = []
    agent_name = default_agent
    framework = "opentelemetry"
    model = None
    status = "success"
    input_text = None
    output_text = None
    total_latency = 0

    for rs in resource_spans:
        resource = rs.get("resource", {}) or {}
        attrs = _attr_map(resource.get("attributes", []))
        agent_name = attrs.get("service.name") or attrs.get("agent.name") or agent_name
        framework = attrs.get("framework") or framework

        for scope_span in rs.get("scopeSpans") or rs.get("scope_spans") or []:
            scope_name = (scope_span.get("scope") or {}).get("name", "")
            for span in scope_span.get("spans") or []:
                name = span.get("name", "span")
                span_attrs = _attr_map(span.get("attributes", []))
                span_type = _classify_span(name, span_attrs, scope_name)
                start_ns = int(span.get("startTimeUnixNano") or span.get("start_time_unix_nano") or 0)
                end_ns = int(span.get("endTimeUnixNano") or span.get("end_time_unix_nano") or 0)
                latency_ms = max(0, (end_ns - start_ns) // 1_000_000)
                total_latency += latency_ms
                span_status = (span.get("status") or {}).get("code", "OK")
                if span_status in ("ERROR", "STATUS_CODE_ERROR", 2):
                    status = "failed"

                if span_type == "llm":
                    model = span_attrs.get("gen_ai.request.model") or span_attrs.get("model") or model
                    input_text = input_text or span_attrs.get("gen_ai.prompt") or span_attrs.get("input")
                    output_text = output_text or span_attrs.get("gen_ai.completion") or span_attrs.get("output")

                spans.append(
                    IngestSpan(
                        name=name,
                        span_type=span_type,
                        status="failed" if span_status in ("ERROR", "STATUS_CODE_ERROR", 2) else "success",
                        latency_ms=latency_ms,
                        attributes=span_attrs,
                        token_usage={
                            k: int(span_attrs[k])
                            for k in ("input_tokens", "output_tokens", "total_tokens")
                            if k in span_attrs and str(span_attrs[k]).isdigit()
                        },
                    )
                )
                for ev in span.get("events") or []:
                    ev_attrs = _attr_map(ev.get("attributes", []))
                    events.append(
                        IngestEvent(
                            event_type=ev.get("name", "otel.event"),
                            event_data=ev_attrs,
                        )
                    )

    return IngestTraceRequest(
        agent=IngestAgentMeta(name=agent_name, framework=framework),
        input=input_text,
        output=output_text,
        status=status,
        latency_ms=total_latency or None,
        model=model,
        spans=spans,
        events=events,
    )


def _attr_map(attrs: list) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for a in attrs:
        key = a.get("key")
        val = a.get("value", {})
        if not key:
            continue
        if "stringValue" in val:
            out[key] = val["stringValue"]
        elif "intValue" in val:
            out[key] = val["intValue"]
        elif "doubleValue" in val:
            out[key] = val["doubleValue"]
        elif "boolValue" in val:
            out[key] = val["boolValue"]
    return out


def _classify_span(name: str, attrs: dict, scope: str) -> str:
    n = name.lower()
    if "llm" in n or "chat" in n or "completion" in n or attrs.get("gen_ai.request.model"):
        return "llm"
    if "tool" in n or "function" in n or scope.lower().find("tool") >= 0:
        return "tool"
    if "error" in n or attrs.get("error"):
        return "error"
    return "custom"
