#!/usr/bin/env python3
"""
Traceplane demo company generator.

Seeds ResearchAgent, SupportAgent, and CodeReviewAgent with realistic production-like
telemetry: successes, failures, retries, latency spikes, cost spikes, replay trees,
incidents, and evaluations.

Usage:
  export TRACEPLANE_API_KEY=aoh_...
  export TRACEPLANE_BASE_URL=http://127.0.0.1:8000/api/v1
  export DEMO_EMAIL=your@email.com
  export DEMO_PASSWORD=your-password
  python scripts/demo_company.py
"""

from __future__ import annotations

import os
import random
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sdk"))
sys.path.insert(0, str(ROOT / "scripts"))

from agentops_hub import AgentOps  # noqa: E402
from demo_shared import explicit_spans, rich_events  # noqa: E402

BASE = os.environ.get(
    "TRACEPLANE_BASE_URL", os.environ.get("AGENTOPS_BASE_URL", "http://127.0.0.1:8000/api/v1")
).rstrip("/")
API_KEY = os.environ.get("TRACEPLANE_API_KEY", os.environ.get("AGENTOPS_API_KEY", ""))
EMAIL = os.environ.get("DEMO_EMAIL", "demo@company.com")
PASSWORD = os.environ.get("DEMO_PASSWORD", "demo-pass-123")

AGENTS = [
    ("ResearchAgent", "langgraph", "openai", ["research", "rag"]),
    ("SupportAgent", "crewai", "anthropic", ["support", "tickets"]),
    ("CodeReviewAgent", "openai-agents", "openai", ["code", "review"]),
]
MODELS = ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4"]


def require_api_key() -> str:
    if not API_KEY:
        raise SystemExit("Set TRACEPLANE_API_KEY (Settings → API Keys)")
    return API_KEY


def login_session(client: httpx.Client) -> dict[str, str]:
    response = client.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if response.status_code != 200:
        print(f"  ⚠ Login failed ({response.status_code}) — set DEMO_EMAIL/DEMO_PASSWORD")
        return {}
    token = response.json().get("access_token", "")
    csrf = response.cookies.get("tp_csrf_token")
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    if csrf:
        headers["X-CSRF-Token"] = csrf
    return headers


def send_success(
    sdk: AgentOps, name: str, framework: str, provider: str, tags: list[str], *, model: str | None = None
) -> dict:
    model = model or random.choice(MODELS)
    prompt = f"[{name}] request #{random.randint(10000, 99999)}"
    with sdk.trace(
        agent=name,
        model=model,
        framework=framework,
        provider=provider,
        owner="acme-corp",
        tags=["demo-company", *tags],
    ) as span:
        span.set_input(prompt)
        span.set_output(f"Completed {prompt[:28]}…")
        span.set_tokens(
            input_tokens=random.randint(120, 600),
            output_tokens=random.randint(60, 280),
            cached_tokens=random.randint(0, 80),
        )
        for event in rich_events(model=model):
            span.add_event(event["event_type"], **event["event_data"])
    return span.result or {}


def send_failure(
    sdk: AgentOps,
    name: str,
    framework: str,
    provider: str,
    *,
    reason: str,
    latency_ms: int = 30000,
    model: str = "claude-sonnet-4",
) -> dict:
    return sdk.ingest_trace(
        agent=name,
        model=model,
        framework=framework,
        provider=provider,
        owner="acme-corp",
        tags=["demo-company", "failure"],
        input=f"[{name}] {reason}",
        output=f"Error: {reason}",
        status="failed",
        latency_ms=latency_ms,
        token_usage={"input_tokens": 500, "output_tokens": 0, "total_tokens": 500},
        events=[
            {"event_type": "execution.started", "event_data": {}},
            {"event_type": "error.agent", "event_data": {"message": reason}},
            {"event_type": "execution.failed", "event_data": {"reason": reason}},
        ],
    )


def send_retry_then_success(sdk: AgentOps, name: str, framework: str, provider: str) -> list[dict]:
    """Simulate a failed attempt followed by a successful retry."""
    fail = send_failure(
        sdk, name, framework, provider, reason="RateLimitError: 429 — retrying", latency_ms=2100
    )
    time.sleep(0.15)
    with sdk.trace(agent=name, model="gpt-4o-mini", framework=framework, provider=provider, owner="acme-corp", tags=["demo-company", "retry"]) as span:
        span.add_event("retry.scheduled", attempt=2, delay_ms=500)
        span.set_input(f"[{name}] retry after rate limit")
        span.set_output("Succeeded on retry")
        span.set_tokens(input_tokens=180, output_tokens=90)
    return [fail, span.result or {}]


def send_latency_spike(sdk: AgentOps, name: str, framework: str, provider: str) -> dict:
    return sdk.ingest_trace(
        agent=name,
        model="gpt-4o",
        framework=framework,
        provider=provider,
        owner="acme-corp",
        tags=["demo-company", "latency-spike"],
        input=f"[{name}] deep multi-hop analysis",
        output="Analysis complete after slow upstream",
        status="success",
        latency_ms=8200,
        token_usage={"input_tokens": 1200, "output_tokens": 400, "total_tokens": 1600},
        events=[
            {"event_type": "model.call.started", "event_data": {"model": "gpt-4o"}},
            {"event_type": "model.call.completed", "event_data": {"latency_ms": 7800}},
        ],
        spans=[
            {"span_id": "root", "name": name, "span_type": "root", "status": "success", "latency_ms": 8200},
            {"span_id": "llm", "parent_span_id": "root", "name": "gpt-4o", "span_type": "llm", "status": "success", "latency_ms": 7800},
        ],
    )


def send_cost_spike(sdk: AgentOps, name: str, framework: str, provider: str) -> dict:
    return sdk.ingest_trace(
        agent=name,
        model="gpt-4o",
        framework=framework,
        provider=provider,
        owner="acme-corp",
        tags=["demo-company", "cost-spike"],
        input=f"[{name}] large context batch review",
        output="Batch review complete",
        status="success",
        latency_ms=3400,
        estimated_cost=0.0842,
        token_usage={"input_tokens": 18000, "output_tokens": 4200, "total_tokens": 22200},
    )


def seed_traces(sdk: AgentOps) -> list[dict]:
    results: list[dict] = []

    print("  Baseline traffic (3 agents × 4 successes)")
    for name, framework, provider, tags in AGENTS:
        for _ in range(4):
            r = send_success(sdk, name, framework, provider, tags)
            results.append(r)
            time.sleep(0.1)

    print("  Failures + retries (SupportAgent)")
    results.extend(
        send_retry_then_success(sdk, "SupportAgent", "crewai", "anthropic")
    )
    for _ in range(3):
        results.append(
            send_failure(sdk, "SupportAgent", "crewai", "anthropic", reason="tool billing_lookup timeout")
        )
        time.sleep(0.1)

    print("  Latency + cost spikes (CodeReviewAgent)")
    results.append(send_latency_spike(sdk, "CodeReviewAgent", "openai-agents", "openai"))
    results.append(send_cost_spike(sdk, "CodeReviewAgent", "openai-agents", "openai"))

    print("  Session replay tree (ResearchAgent)")
    replay = sdk.ingest_trace(
        agent="ResearchAgent",
        model="gpt-4o",
        framework="langgraph",
        provider="openai",
        input="Compare Q1 vs Q2 churn drivers across segments",
        output="Replay-ready multi-hop research complete",
        status="success",
        latency_ms=4200,
        token_usage={"input_tokens": 980, "output_tokens": 410, "cached_tokens": 200, "total_tokens": 1390},
        spans=explicit_spans(model="gpt-4o"),
        events=rich_events(model="gpt-4o"),
        tags=["demo-company", "replay"],
    )
    results.append(replay)

    print(f"  Total executions seeded: {len(results)}")
    return results


def seed_control_plane(client: httpx.Client, headers: dict[str, str], replay_id: str | None) -> None:
    if not headers:
        return

    r = client.post(f"{BASE}/incidents/detect", headers=headers)
    if r.status_code == 200:
        created = r.json()
        print(f"  ✓ Incident detection — {len(created)} incident(s)")
    else:
        print(f"  ⚠ Incident detect ({r.status_code})")

    if replay_id:
        r = client.get(f"{BASE}/executions/{replay_id}/session-replay", headers=headers)
        if r.status_code == 200:
            body = r.json()
            print(f"  ✓ Session replay — {body.get('step_count', 0)} steps")
        else:
            print(f"  ⚠ Session replay ({r.status_code})")

    eval_payload = {
        "name": "CodeReview quality gate",
        "description": "Demo evaluation for PR review agent",
        "criteria": ["accuracy", "latency", "cost"],
    }
    r = client.post(f"{BASE}/evaluations", json=eval_payload, headers=headers)
    print(f"  {'✓' if r.status_code in (200, 201) else '⚠'} Evaluation ({r.status_code})")


def main() -> int:
    require_api_key()
    sdk = AgentOps(api_key=API_KEY, base_url=BASE)
    http = httpx.Client(base_url=BASE, timeout=30.0)

    print("Traceplane — demo company seed")
    print(f"API: {BASE}")
    print()

    print("1. Telemetry")
    traces = seed_traces(sdk)
    replay_id = str(traces[-1].get("execution_id", "")) if traces else None
    print()

    print("2. Control plane")
    headers = login_session(http)
    seed_control_plane(http, headers, replay_id)

    print()
    print(f"Done — {len(traces)} executions. Open http://localhost:3000/analytics")
    sdk.close()
    http.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
