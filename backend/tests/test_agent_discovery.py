from app.schemas.ingest import IngestAgentMeta, IngestEvent, IngestSpan, IngestTraceRequest
from app.services.agent_discovery import discover_agent_meta


def test_infers_framework_from_langgraph_event():
    data = IngestTraceRequest(
        agent=IngestAgentMeta(name="ResearchBot"),
        events=[IngestEvent(event_type="langgraph.node.enter", event_data={"node": "plan"})],
    )
    meta = discover_agent_meta(data)
    assert meta.framework == "langgraph"


def test_infers_model_from_llm_span():
    data = IngestTraceRequest(
        agent=IngestAgentMeta(name="Bot"),
        spans=[
            IngestSpan(span_id="l1", name="gpt-4o", span_type="llm", attributes={"model": "gpt-4o"}),
        ],
    )
    meta = discover_agent_meta(data)
    assert meta.model == "gpt-4o"
    assert meta.provider == "openai"


def test_explicit_metadata_takes_precedence():
    data = IngestTraceRequest(
        agent=IngestAgentMeta(name="Bot", framework="crewai", model="claude-sonnet-4", provider="anthropic"),
    )
    meta = discover_agent_meta(data)
    assert meta.framework == "crewai"
    assert meta.model == "claude-sonnet-4"
    assert meta.provider == "anthropic"


def test_infers_pydanticai_from_event():
    data = IngestTraceRequest(
        agent=IngestAgentMeta(name="Bot"),
        events=[IngestEvent(event_type="pydantic_ai.agent.run", event_data={})],
    )
    assert discover_agent_meta(data).framework == "pydanticai"


def test_infers_agno_from_agent_name():
    data = IngestTraceRequest(agent=IngestAgentMeta(name="AgnoResearchBot"))
    assert discover_agent_meta(data).framework == "agno"
