# Public SDK base URL for production (override in local dev with TRACEPLANE_BASE_URL)
import os

from traceplane.client import AgentOps, TraceSpan, Traceplane

_DEFAULT_BASE_URL = os.environ.get("TRACEPLANE_BASE_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")

_client: Traceplane | None = None


def init(
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float = 30.0,
) -> Traceplane:
    global _client
    resolved_key = api_key or os.environ.get("TRACEPLANE_API_KEY", "")
    if not resolved_key:
        raise ValueError("TRACEPLANE_API_KEY is required")
    resolved_base = (base_url or _DEFAULT_BASE_URL).rstrip("/")
    _client = Traceplane(api_key=resolved_key, base_url=resolved_base, timeout=timeout)
    return _client


def _require_client() -> Traceplane:
    if _client is None:
        raise RuntimeError("Call traceplane.init(api_key=...) before using the SDK")
    return _client


def trace(agent: str, model: str | None = None, **agent_meta) -> TraceSpan:
    return _require_client().trace(agent=agent, model=model, **agent_meta)


def ingest_trace(**kwargs):
    return _require_client().ingest_trace(**kwargs)


__all__ = ["Traceplane", "AgentOps", "TraceSpan", "init", "trace", "ingest_trace"]
__version__ = "0.2.0"
