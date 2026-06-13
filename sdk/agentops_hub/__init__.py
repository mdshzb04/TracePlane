"""Deprecated — use `traceplane` package. Kept for backward compatibility."""

from traceplane import AgentOps, TraceSpan, Traceplane, init, ingest_trace, trace

__all__ = ["Traceplane", "AgentOps", "TraceSpan", "init", "trace", "ingest_trace"]
