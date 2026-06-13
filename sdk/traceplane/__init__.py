from traceplane.client import AgentOps, TraceSpan, Traceplane

_client: Traceplane | None = None


def init(
    api_key: str,
    base_url: str = "http://127.0.0.1:8000/api/v1",
    timeout: float = 30.0,
) -> Traceplane:
    global _client
    _client = Traceplane(api_key=api_key, base_url=base_url, timeout=timeout)
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
