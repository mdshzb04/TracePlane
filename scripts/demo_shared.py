"""Shared telemetry helpers for demo/seed scripts."""


def rich_events(*, model: str, tool_name: str = "web_search") -> list[dict]:
    """Events that produce llm, tool, and completion spans in Trace Explorer."""
    return [
        {"event_type": "execution.started", "event_data": {}},
        {"event_type": "tool.invoked", "event_data": {"tool": tool_name, "query": "latest news"}},
        {"event_type": "tool.completed", "event_data": {"tool": tool_name, "latency_ms": 120}},
        {
            "event_type": "model.call.completed",
            "event_data": {
                "model": model,
                "input_tokens": 180,
                "output_tokens": 95,
                "cached_tokens": 40,
                "latency_ms": 840,
            },
        },
        {"event_type": "output.generated", "event_data": {"preview": "done"}},
        {"event_type": "execution.completed", "event_data": {"status": "success"}},
    ]


def explicit_spans(*, model: str) -> list[dict]:
    """Parent/child span tree for Trace Explorer waterfall."""
    return [
        {
            "span_id": "root",
            "name": "agent.run",
            "span_type": "root",
            "status": "success",
            "latency_ms": 1200,
        },
        {
            "span_id": "tool-1",
            "parent_span_id": "root",
            "name": "web_search",
            "span_type": "tool",
            "status": "success",
            "latency_ms": 200,
            "attributes": {"tool": "web_search"},
        },
        {
            "span_id": "llm-1",
            "parent_span_id": "root",
            "name": model,
            "span_type": "llm",
            "status": "success",
            "latency_ms": 900,
            "token_usage": {"input_tokens": 200, "output_tokens": 80, "cached_tokens": 50},
            "estimated_cost": 0.0024,
        },
    ]
