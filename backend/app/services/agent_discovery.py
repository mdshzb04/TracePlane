"""Infer agent metadata from first SDK telemetry — no manual registry required."""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.ingest import IngestTraceRequest

_FRAMEWORK_EVENT_HINTS: tuple[tuple[str, str], ...] = (
    ("langgraph.", "langgraph"),
    ("graph.node", "langgraph"),
    ("crewai.", "crewai"),
    ("crew.", "crewai"),
    ("openai.agent", "openai-agents"),
    ("agents.run", "openai-agents"),
    ("openai-agents", "openai-agents"),
    ("autogen.", "autogen"),
    ("pydantic_ai.", "pydanticai"),
    ("pydanticai.", "pydanticai"),
    ("agno.", "agno"),
    ("opentelemetry", "opentelemetry"),
)

_MODEL_PROVIDER_HINTS: tuple[tuple[str, str], ...] = (
    ("gpt", "openai"),
    ("o1", "openai"),
    ("o3", "openai"),
    ("claude", "anthropic"),
    ("gemini", "google"),
    ("llama", "meta"),
    ("mistral", "mistral"),
    ("nvidia", "nvidia"),
    ("nemotron", "nvidia"),
)


@dataclass(frozen=True)
class DiscoveredAgentMeta:
    framework: str
    model: str
    provider: str | None


def discover_agent_meta(data: IngestTraceRequest) -> DiscoveredAgentMeta:
    """Infer framework, primary model, and provider from telemetry payload."""
    framework = _infer_framework(data)
    model = _infer_model(data)
    provider = _infer_provider(data, model)
    return DiscoveredAgentMeta(framework=framework, model=model, provider=provider)


def _infer_framework(data: IngestTraceRequest) -> str:
    if data.agent.framework:
        return data.agent.framework.strip().lower()

    for event in data.events:
        event_type = event.event_type.lower()
        for prefix, framework in _FRAMEWORK_EVENT_HINTS:
            if prefix in event_type:
                return framework
        fw = (event.event_data or {}).get("framework")
        if isinstance(fw, str) and fw.strip():
            return fw.strip().lower()

    for span in data.spans:
        fw = (span.attributes or {}).get("framework")
        if isinstance(fw, str) and fw.strip():
            return fw.strip().lower()

    name = data.agent.name.lower()
    if "langgraph" in name:
        return "langgraph"
    if "crew" in name:
        return "crewai"
    if "autogen" in name:
        return "autogen"
    if "pydantic" in name:
        return "pydanticai"
    if "agno" in name:
        return "agno"

    return "custom"


def _infer_model(data: IngestTraceRequest) -> str:
    if data.model and data.model.strip():
        return data.model.strip()
    if data.agent.model and data.agent.model.strip():
        return data.agent.model.strip()

    for event in data.events:
        if event.event_type in ("model.call.completed", "llm.call", "model.call"):
            model = (event.event_data or {}).get("model")
            if isinstance(model, str) and model.strip():
                return model.strip()

    for span in data.spans:
        if span.span_type == "llm":
            model = (span.attributes or {}).get("model") or span.name
            if isinstance(model, str) and model.strip():
                return model.strip()

    return "unknown"


def _infer_provider(data: IngestTraceRequest, model: str) -> str | None:
    if data.agent.provider and data.agent.provider.strip():
        return data.agent.provider.strip().lower()

    model_lower = model.lower()
    for hint, provider in _MODEL_PROVIDER_HINTS:
        if hint in model_lower:
            return provider

    for event in data.events:
        provider = (event.event_data or {}).get("provider")
        if isinstance(provider, str) and provider.strip():
            return provider.strip().lower()

    return None
