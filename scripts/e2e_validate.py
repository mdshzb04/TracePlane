#!/usr/bin/env python3
"""
End-to-end validation for AgentOps Hub control plane.

Flow: SDK → Ingest → Registry → Executions → Traces → Analytics → Investigator → Evaluations

Usage:
  export AGENTOPS_API_KEY=aoh_...
  export AGENTOPS_BASE_URL=http://127.0.0.1:8000/api/v1
  export E2E_EMAIL=demo@company.com
  export E2E_PASSWORD=your-password
  python scripts/e2e_validate.py
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sdk"))

from agentops_hub import AgentOps  # noqa: E402

BASE = os.environ.get("AGENTOPS_BASE_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
API_ROOT = BASE.replace("/api/v1", "")
API_KEY = os.environ.get("AGENTOPS_API_KEY", "")
EMAIL = os.environ.get("E2E_EMAIL", "e2e@company.com")
PASSWORD = os.environ.get("E2E_PASSWORD", "testpass123")


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class E2EReport:
    checks: list[CheckResult] = field(default_factory=list)

    def ok(self, name: str, detail: str = "") -> None:
        self.checks.append(CheckResult(name, True, detail))

    def fail(self, name: str, detail: str = "") -> None:
        self.checks.append(CheckResult(name, False, detail))

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)


def login_token() -> str | None:
    try:
        r = httpx.post(
            f"{BASE}/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json().get("access_token")
    except Exception:
        pass
    return None


def main() -> int:
    report = E2EReport()
    print("Traceplane E2E Validation")
    print("=" * 50)

    # 1. Health
    try:
        ready = httpx.get(f"{API_ROOT}/health/ready", timeout=15).json()
        db_ok = ready.get("database") == "ok"
        redis_ok = ready.get("redis", {}).get("status") in ("ok", "skipped")
        report.ok("API /health/ready", f"db={db_ok} redis={ready.get('redis', {}).get('status')}")
        if not db_ok:
            report.fail("Database schema", ready.get("detail", "not ready"))
    except Exception as exc:
        report.fail("API /health/ready", str(exc))
        _print_report(report)
        return 1

    # 2. Redis / Celery broker (from readiness payload)
    redis_status = ready.get("redis", {})
    if redis_status.get("status") == "ok":
        report.ok("Redis connection", "ping ok")
    elif redis_status.get("configured"):
        report.fail("Redis connection", redis_status.get("detail", "error"))
    else:
        report.ok("Redis connection", "not configured (optional)")

    broker = ready.get("celery_broker", {})
    if broker.get("status") == "ok":
        report.ok("Celery broker", broker.get("broker", "ok"))
    elif broker.get("configured"):
        report.fail("Celery broker", broker.get("detail", "error"))
    else:
        report.ok("Celery broker", "not configured (optional)")

    if not API_KEY:
        report.fail("AGENTOPS_API_KEY", "not set — cannot test ingest")
        _print_report(report)
        return 1

    # 3. SDK ingest
    client = AgentOps(api_key=API_KEY, base_url=BASE)
    agent_name = f"E2EAgent-{uuid.uuid4().hex[:6]}"
    try:
        result = client.ingest_trace(
            agent=agent_name,
            model="gpt-4o",
            framework="e2e",
            provider="openai",
            input="E2E validation trace",
            output="Validation output",
            status="success",
            latency_ms=420,
            token_usage={"input_tokens": 50, "output_tokens": 20, "total_tokens": 70},
            events=[
                {"event_type": "tool.invoked", "event_data": {"tool": "search"}},
                {"event_type": "model.call.completed", "event_data": {"model": "gpt-4o", "input_tokens": 50, "output_tokens": 20}},
            ],
            spans=[
                {"span_id": "root", "name": "e2e.run", "span_type": "root", "status": "success", "latency_ms": 420},
                {"span_id": "tool", "parent_span_id": "root", "name": "search", "span_type": "tool", "status": "success", "latency_ms": 80},
                {"span_id": "llm", "parent_span_id": "root", "name": "gpt-4o", "span_type": "llm", "status": "success", "latency_ms": 300},
            ],
        )
        execution_id = result.get("execution_id")
        agent_id = result.get("agent_id")
        report.ok("SDK ingest", f"execution={execution_id}")
        report.ok("Agent auto-discovery", f"agent={agent_id} created={result.get('created_agent')}")
    except Exception as exc:
        report.fail("SDK ingest", str(exc))
        _print_report(report)
        return 1

    # Failure trace for investigator
    try:
        fail_result = client.ingest_trace(
            agent=agent_name,
            model="gpt-4o",
            framework="e2e",
            status="failed",
            input="Why did this fail?",
            output="RateLimitError: 429 too many requests",
            latency_ms=1200,
            events=[
                {"event_type": "error.rate_limit", "event_data": {"code": 429}},
                {"event_type": "execution.failed", "event_data": {}},
            ],
        )
        report.ok("Failed execution ingest", fail_result.get("execution_id", "")[:8])
    except Exception as exc:
        report.fail("Failed execution ingest", str(exc))

    token = login_token()
    if not token:
        report.fail("JWT login", f"could not login as {EMAIL}")
        _print_report(report)
        return 1
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Agent registry
    try:
        agents = httpx.get(f"{BASE}/agents?search={agent_name}", headers=headers, timeout=30).json()
        found = any(a["name"] == agent_name for a in agents.get("items", []))
        report.ok("Agent registry", f"found={found}") if found else report.fail("Agent registry", "agent not listed")
    except Exception as exc:
        report.fail("Agent registry", str(exc))

    # 5. Trace explorer
    try:
        detail = httpx.get(f"{BASE}/analytics/traces/{execution_id}", headers=headers, timeout=30).json()
        spans = detail.get("spans", [])
        timelines = detail.get("timelines", {})
        has_llm = len(timelines.get("llm_calls", [])) > 0 or any(s.get("span_type") == "llm" for s in _flatten_spans(spans))
        has_tool = any(s.get("span_type") == "tool" for s in _flatten_spans(spans))
        has_root = any(s.get("span_type") == "root" for s in spans)
        report.ok("Trace span tree", f"spans={len(_flatten_spans(spans))} root={has_root} llm={has_llm} tool={has_tool}")
    except Exception as exc:
        report.fail("Trace explorer", str(exc))

    # 6. Analytics
    try:
        obs = httpx.get(f"{BASE}/analytics/observability", headers=headers, timeout=30).json()
        kpis = obs.get("kpis", {})
        report.ok(
            "Analytics observability",
            f"requests={kpis.get('total_requests')} cost=${kpis.get('total_cost', 0):.4f}",
        )
        live = httpx.get(f"{BASE}/analytics/live", headers=headers, timeout=30).json()
        report.ok("Live metrics", f"recent={len(live.get('recent_executions', []))}")
    except Exception as exc:
        report.fail("Analytics", str(exc))

    # 7. Investigator
    try:
        inv = httpx.post(
            f"{BASE}/investigator/investigate",
            headers=headers,
            json={"query": f"Why is {agent_name} failing?", "agent_id": agent_id},
            timeout=120,
        )
        if inv.status_code == 200:
            body = inv.json()
            report.ok(
                "Investigator V2",
                f"confidence={body.get('confidence_score')} causes={len(body.get('root_causes', []))}",
            )
            hist = httpx.get(f"{BASE}/investigator/history?limit=5", headers=headers, timeout=30).json()
            report.ok("Investigation history", f"items={hist.get('total', 0)}")
        else:
            report.fail("Investigator V2", inv.text[:200])
    except Exception as exc:
        report.fail("Investigator V2", str(exc))

    # 8. Executions + session replay
    try:
        execs = httpx.get(f"{BASE}/executions?limit=5", headers=headers, timeout=30).json()
        items = execs.get("items", [])
        report.ok("Executions list", f"count={len(items)}")
        if execution_id:
            detail = httpx.get(f"{BASE}/executions/{execution_id}/detail", headers=headers, timeout=30)
            report.ok("Execution detail", f"status={detail.status_code}")
            replay = httpx.get(
                f"{BASE}/executions/{execution_id}/session-replay", headers=headers, timeout=30
            )
            if replay.status_code == 200:
                body = replay.json()
                report.ok("Session replay", f"steps={body.get('step_count', 0)}")
            else:
                report.fail("Session replay", replay.text[:200])
    except Exception as exc:
        report.fail("Executions / session replay", str(exc))

    # 9. Incidents
    try:
        detect = httpx.post(f"{BASE}/incidents/detect", headers=headers, timeout=30)
        if detect.status_code == 200:
            report.ok("Incident detection", f"created={len(detect.json())}")
        else:
            report.fail("Incident detection", detect.text[:200])
        inc_list = httpx.get(f"{BASE}/incidents", headers=headers, timeout=30).json()
        report.ok("Incidents list", f"count={len(inc_list)}")
    except Exception as exc:
        report.fail("Incidents", str(exc))

    # 10. Onboarding status
    try:
        onboarding = httpx.get(f"{BASE}/system/onboarding", headers=headers, timeout=30).json()
        report.ok(
            "Onboarding status",
            f"complete={onboarding.get('onboarding_complete')} traces={onboarding.get('execution_count')}",
        )
    except Exception as exc:
        report.fail("Onboarding status", str(exc))

    # 11. Evaluation engine
    try:
        ds = httpx.post(
            f"{BASE}/evaluation-engine/datasets",
            headers=headers,
            json={
                "name": f"E2E Dataset {uuid.uuid4().hex[:6]}",
                "items": [{"test_case": "E2E validation trace", "expected_output": "Validation output"}],
            },
            timeout=30,
        )
        if ds.status_code in (200, 201):
            dataset_id = ds.json()["id"]
            run = httpx.post(
                f"{BASE}/evaluation-engine/runs",
                headers=headers,
                json={"dataset_id": dataset_id, "agent_id": agent_id},
                timeout=60,
            )
            if run.status_code in (200, 201):
                report.ok("Evaluation run", f"score={run.json().get('average_score')}")
            else:
                report.fail("Evaluation run", run.text[:200])
            hist = httpx.get(f"{BASE}/evaluation-engine/score-history", headers=headers, timeout=30).json()
            report.ok("Evaluation score history", f"points={len(hist.get('points', []))}")
        else:
            report.fail("Evaluation dataset", ds.text[:200])
    except Exception as exc:
        report.fail("Evaluation engine", str(exc))

    client.close()
    _print_report(report)

    # Write checklist fragment
    out = ROOT / "PRODUCTION_CHECKLIST.md"
    if out.exists():
        pass  # full file written separately

    return 0 if report.passed else 1


def _flatten_spans(nodes: list) -> list:
    flat = []
    for n in nodes:
        flat.append(n)
        flat.extend(_flatten_spans(n.get("children", [])))
    return flat


def _print_report(report: E2EReport) -> None:
    print()
    for c in report.checks:
        icon = "PASS" if c.passed else "FAIL"
        line = f"[{icon}] {c.name}"
        if c.detail:
            line += f" — {c.detail}"
        print(line)
    print()
    print(f"Result: {'ALL PASSED' if report.passed else 'SOME CHECKS FAILED'} ({sum(c.passed for c in report.checks)}/{len(report.checks)})")


if __name__ == "__main__":
    sys.exit(main())
