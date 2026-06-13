#!/usr/bin/env python3
"""
AgentOps Hub demo telemetry generator.

Sends realistic traces to populate Agent Registry, Executions, Trace Explorer,
Dashboard analytics, and Evaluation data.

Usage:
  export AGENTOPS_API_KEY=aoh_...
  export AGENTOPS_BASE_URL=http://127.0.0.1:8000/api/v1   # optional
  python scripts/demo_agent.py
"""

from __future__ import annotations

import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sdk"))
sys.path.insert(0, str(ROOT / "scripts"))

from agentops_hub import AgentOps  # noqa: E402
from demo_shared import explicit_spans, rich_events  # noqa: E402

MODELS = ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4", "gemini-2.0-flash"]
AGENTS = [
    ("ResearchAgent", "langgraph", "openai"),
    ("SupportAgent", "crewai", "anthropic"),
    ("CodeReviewAgent", "openai-agents", "openai"),
    ("DataPipelineAgent", "custom", "nvidia"),
]


def get_client() -> AgentOps:
    key = os.environ.get("AGENTOPS_API_KEY", "")
    if not key:
        raise SystemExit(
            "Set AGENTOPS_API_KEY — create one at Settings → API Keys in the control plane"
        )
    base = os.environ.get("AGENTOPS_BASE_URL", "http://127.0.0.1:8000/api/v1")
    return AgentOps(api_key=key, base_url=base)


def send_success(client: AgentOps, name: str, framework: str, provider: str, model: str) -> dict:
    prompt = f"[{name}] Process request batch {random.randint(1000, 9999)}"
    with client.trace(
        agent=name,
        model=model,
        framework=framework,
        provider=provider,
        owner="demo-team",
        tags=["demo", framework],
    ) as span:
        span.set_input(prompt)
        span.set_output(f"Completed: {prompt[:40]}...")
        span.set_tokens(
            input_tokens=random.randint(80, 400),
            output_tokens=random.randint(40, 200),
            cached_tokens=random.randint(0, 50),
        )
        for e in rich_events(model=model):
            span.add_event(e["event_type"], **e["event_data"])
    return span.result or {}


def send_failure(client: AgentOps, name: str, framework: str, provider: str, model: str) -> dict:
    return client.ingest_trace(
        agent=name,
        model=model,
        framework=framework,
        provider=provider,
        owner="demo-team",
        tags=["demo", "failure"],
        input="Trigger edge case for investigator demo",
        output="TimeoutError: upstream LLM gateway returned 504 after 30s",
        status="failed",
        latency_ms=30000,
        token_usage={"input_tokens": 500, "output_tokens": 0, "total_tokens": 500},
        events=[
            {"event_type": "execution.started", "event_data": {}},
            {"event_type": "model.call.started", "event_data": {"model": model}},
            {"event_type": "error.timeout", "event_data": {"code": 504, "message": "gateway timeout"}},
            {"event_type": "execution.failed", "event_data": {"reason": "timeout"}},
        ],
        spans=[
            {"span_id": "root", "name": name, "span_type": "root", "status": "failed", "latency_ms": 30000},
            {"span_id": "llm", "parent_span_id": "root", "name": model, "span_type": "llm", "status": "failed", "latency_ms": 28000},
            {"span_id": "err", "parent_span_id": "root", "name": "gateway timeout", "span_type": "error", "status": "failed", "latency_ms": 100},
        ],
    )


def send_span_tree(client: AgentOps, model: str) -> dict:
    return client.ingest_trace(
        agent="ResearchAgent",
        model=model,
        framework="langgraph",
        provider="openai",
        input="Multi-hop research with tools",
        output="Span tree demo complete",
        status="success",
        latency_ms=1500,
        token_usage={"input_tokens": 220, "output_tokens": 90, "cached_tokens": 30, "total_tokens": 310},
        spans=explicit_spans(model=model),
        events=rich_events(model=model),
    )


def main() -> None:
    client = get_client()
    print("AgentOps Hub — demo telemetry")
    print(f"Target: {client.base_url}")
    print()

    results: list[dict] = []

    for name, framework, provider in AGENTS:
        model = random.choice(MODELS)
        r = send_success(client, name, framework, provider, model)
        results.append(r)
        print(f"  ✓ {name} ({framework}) — execution {str(r.get('execution_id', ''))[:8]}")
        time.sleep(0.3)

    fail = send_failure(client, "SupportAgent", "crewai", "anthropic", "claude-sonnet-4")
    results.append(fail)
    print(f"  ✗ SupportAgent failure — execution {str(fail.get('execution_id', ''))[:8]}")

    tree = send_span_tree(client, "gpt-4o")
    results.append(tree)
    print(f"  ✓ ResearchAgent span tree — execution {str(tree.get('execution_id', ''))[:8]}")

    print()
    print(f"Sent {len(results)} traces. Open http://localhost:3000/analytics to view metrics.")
    client.close()


if __name__ == "__main__":
    main()
