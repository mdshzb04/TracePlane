from __future__ import annotations

import time
from contextlib import ContextDecorator
from typing import Any, Optional

import httpx


class TraceSpan(ContextDecorator):
  """Active trace span — records input/output and posts telemetry to Traceplane."""

  def __init__(self, client: "Traceplane", agent: str, model: Optional[str] = None, **agent_meta: Any):
    self._client = client
    self.agent = agent
    self.model = model
    self.agent_meta = agent_meta
    self.input: Optional[str] = None
    self.output: Optional[str] = None
    self.status = "success"
    self.events: list[dict[str, Any]] = []
    self.token_usage: dict[str, int] = {}
    self._start: float = 0.0
    self._result: Optional[dict[str, Any]] = None

  def set_input(self, value: str) -> None:
    self.input = value

  def set_output(self, value: str) -> None:
    self.output = value

  def add_event(self, event_type: str, **event_data: Any) -> None:
    self.events.append({"event_type": event_type, "event_data": event_data})

  def llm_call(
    self,
    model: str | None = None,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
    latency_ms: int | None = None,
  ) -> None:
    self.add_event(
      "model.call.completed",
      model=model or self.model,
      input_tokens=input_tokens,
      output_tokens=output_tokens,
      latency_ms=latency_ms,
    )
    prev_in = self.token_usage.get("input_tokens", 0)
    prev_out = self.token_usage.get("output_tokens", 0)
    self.set_tokens(prev_in + input_tokens, prev_out + output_tokens)

  def tool_call(self, name: str, *, latency_ms: int | None = None, **data: Any) -> None:
    self.add_event("tool.invoked", tool=name, latency_ms=latency_ms, **data)

  def error(self, message: str, *, code: str | None = None, **data: Any) -> None:
    self.status = "failed"
    self.add_event("error.agent", message=message, code=code, **data)
    if not self.output:
      self.output = message

  def span(self, name: str, span_type: str = "custom", **attrs: Any) -> None:
    self.add_event(f"span.{span_type}", name=name, **attrs)

  def set_tokens(self, input_tokens: int = 0, output_tokens: int = 0, cached_tokens: int = 0) -> None:
    total = input_tokens + output_tokens
    self.token_usage = {
      "input_tokens": input_tokens,
      "output_tokens": output_tokens,
      "cached_tokens": cached_tokens,
      "total_tokens": total,
    }

  def __enter__(self) -> "TraceSpan":
    self._start = time.perf_counter()
    self.add_event("execution.started", agent=self.agent)
    return self

  def __exit__(self, exc_type, exc, tb) -> bool:
    latency_ms = int((time.perf_counter() - self._start) * 1000)
    if exc_type is not None:
      self.status = "failed"
      self.output = self.output or str(exc)
    self._result = self._client.ingest_trace(
      agent=self.agent,
      model=self.model,
      input=self.input,
      output=self.output,
      status=self.status,
      latency_ms=latency_ms,
      token_usage=self.token_usage,
      events=self.events,
      **self.agent_meta,
    )
    return False

  @property
  def result(self) -> Optional[dict[str, Any]]:
    return self._result


class Traceplane:
  """Traceplane SDK client — send traces, costs, tokens, and latency from your app."""

  def __init__(
    self,
    api_key: str,
    base_url: str = "http://127.0.0.1:8000/api/v1",
    timeout: float = 30.0,
  ):
    self.api_key = api_key
    self.base_url = base_url.rstrip("/")
    self._client = httpx.Client(
      timeout=timeout,
      headers={"X-API-Key": api_key, "Content-Type": "application/json"},
    )

  def trace(
    self,
    agent: str,
    model: Optional[str] = None,
    **agent_meta: Any,
  ) -> TraceSpan:
    return TraceSpan(self, agent=agent, model=model, **agent_meta)

  def ingest_trace(
    self,
    *,
    agent: str,
    model: Optional[str] = None,
    input: Optional[str] = None,
    output: Optional[str] = None,
    status: str = "success",
    latency_ms: Optional[int] = None,
    token_usage: Optional[dict[str, int]] = None,
    events: Optional[list[dict[str, Any]]] = None,
    spans: Optional[list[dict[str, Any]]] = None,
    framework: Optional[str] = None,
    provider: Optional[str] = None,
    environment: str = "production",
    owner: Optional[str] = None,
    tags: Optional[list[str]] = None,
  ) -> dict[str, Any]:
    payload = {
      "agent": {
        "name": agent,
        "model": model,
        "framework": framework,
        "provider": provider,
        "environment": environment,
        "owner": owner,
        "tags": tags or [],
      },
      "input": input,
      "output": output,
      "status": status,
      "latency_ms": latency_ms,
      "model": model,
      "token_usage": token_usage or {},
      "events": events or [],
      "spans": spans or [],
    }
    response = self._client.post(f"{self.base_url}/ingest/trace", json=payload)
    response.raise_for_status()
    return response.json()

  def close(self) -> None:
    self._client.close()

  def __enter__(self) -> "Traceplane":
    return self

  def __exit__(self, *args: Any) -> None:
    self.close()


# Backward compatibility
AgentOps = Traceplane
