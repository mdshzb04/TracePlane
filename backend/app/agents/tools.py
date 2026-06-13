import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from langchain_core.tools import tool
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.execution import Execution
from app.models.execution_event import ExecutionEvent

logger = logging.getLogger(__name__)

LATENCY_SPIKE_THRESHOLD_MS = 5000
COST_ANOMALY_MULTIPLIER = 3.0


async def _get_agent_info(session: AsyncSession, agent_id: str) -> Optional[dict[str, Any]]:
    result = await session.execute(select(Agent).where(Agent.id == uuid.UUID(agent_id)))
    agent = result.scalars().first()
    if agent is None:
        return None
    return {
        "id": str(agent.id),
        "name": agent.name,
        "description": agent.description,
        "owner": agent.owner,
        "model": agent.model,
        "status": agent.status,
    }


async def _search_agent_by_name(session: AsyncSession, name: str) -> Optional[dict[str, Any]]:
    result = await session.execute(
        select(Agent).where(Agent.name.ilike(f"%{name}%")).limit(1)
    )
    agent = result.scalars().first()
    if agent is None:
        return None
    return {
        "id": str(agent.id),
        "name": agent.name,
        "description": agent.description,
        "owner": agent.owner,
        "model": agent.model,
        "status": agent.status,
    }


async def _get_executions(
    session: AsyncSession,
    agent_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    filters = []
    if agent_id:
        filters.append(Execution.agent_id == uuid.UUID(agent_id))
    if start_date:
        filters.append(Execution.started_at >= start_date)
    if end_date:
        filters.append(Execution.started_at <= end_date)

    where_clause = and_(*filters) if filters else True
    stmt = (
        select(Execution)
        .where(where_clause)
        .order_by(Execution.started_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    executions = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "agent_id": str(e.agent_id),
            "input": e.input,
            "output": e.output,
            "status": e.status,
            "latency_ms": e.latency_ms,
            "token_usage": e.token_usage or {},
            "estimated_cost": float(e.estimated_cost or 0),
            "model": e.model,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
        }
        for e in executions
    ]


async def _get_events(
    session: AsyncSession,
    execution_ids: list[str],
    limit: int = 500,
) -> list[dict[str, Any]]:
    if not execution_ids:
        return []
    uuids = [uuid.UUID(eid) for eid in execution_ids]
    stmt = (
        select(ExecutionEvent)
        .where(ExecutionEvent.execution_id.in_(uuids))
        .order_by(ExecutionEvent.timestamp.asc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    events = result.scalars().all()
    return [
        {
            "id": str(ev.id),
            "execution_id": str(ev.execution_id),
            "event_type": ev.event_type,
            "event_data": ev.event_data or {},
            "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
        }
        for ev in events
    ]


def _analyze_failures(executions: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [e for e in executions if e["status"] == "failed"]
    total = len(executions)
    failure_rate = (len(failed) / total * 100) if total > 0 else 0.0

    failure_types: dict[str, int] = {}
    error_messages: list[str] = []
    for e in failed:
        output = e.get("output") or ""
        error_type = "unknown"
        if "timeout" in output.lower():
            error_type = "timeout"
        elif "rate_limit" in output.lower() or "429" in output:
            error_type = "rate_limit"
        elif "context_length" in output.lower() or "token" in output.lower():
            error_type = "context_overflow"
        elif "connection" in output.lower() or "network" in output.lower():
            error_type = "network_error"
        elif "auth" in output.lower() or "401" in output or "403" in output:
            error_type = "auth_error"
        elif "validation" in output.lower():
            error_type = "validation_error"
        failure_types[error_type] = failure_types.get(error_type, 0) + 1
        if output:
            error_messages.append(output[:200])

    most_common = max(failure_types, key=failure_types.get) if failure_types else None

    return {
        "total_failures": len(failed),
        "failure_rate": round(failure_rate, 2),
        "failure_types": failure_types,
        "most_common_error": most_common,
        "affected_executions": [e["id"] for e in failed[:20]],
        "error_samples": error_messages[:5],
    }


def _analyze_latency(executions: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = sorted(
        [e["latency_ms"] for e in executions if e.get("latency_ms") is not None]
    )
    if not latencies:
        return {
            "avg_latency_ms": 0,
            "p50_latency_ms": 0,
            "p90_latency_ms": 0,
            "p99_latency_ms": 0,
            "max_latency_ms": 0,
            "spike_count": 0,
            "spike_threshold_ms": LATENCY_SPIKE_THRESHOLD_MS,
            "spikes": [],
        }

    n = len(latencies)
    avg = sum(latencies) / n
    p50 = latencies[int(n * 0.5)] if n > 0 else 0
    p90 = latencies[int(n * 0.9)] if n > 0 else 0
    p99 = latencies[int(n * 0.99)] if n > 0 else 0
    max_lat = latencies[-1]

    spikes = [
        {"execution_id": e["id"], "latency_ms": e["latency_ms"], "started_at": e.get("started_at")}
        for e in executions
        if e.get("latency_ms") and e["latency_ms"] > LATENCY_SPIKE_THRESHOLD_MS
    ]

    return {
        "avg_latency_ms": round(avg, 2),
        "p50_latency_ms": p50,
        "p90_latency_ms": p90,
        "p99_latency_ms": p99,
        "max_latency_ms": max_lat,
        "spike_count": len(spikes),
        "spike_threshold_ms": LATENCY_SPIKE_THRESHOLD_MS,
        "spikes": spikes[:20],
    }


def _analyze_prompt_regressions(executions: list[dict[str, Any]]) -> dict[str, Any]:
    return {"version_stats": [], "regression_count": 0, "regressions": []}


def _analyze_costs(executions: list[dict[str, Any]]) -> dict[str, Any]:
    costs = [e.get("estimated_cost", 0) or 0 for e in executions]
    if not costs:
        return {
            "total_cost": 0,
            "avg_cost_per_execution": 0,
            "max_cost_execution": None,
            "cost_trend": [],
            "anomalies": [],
        }

    total = sum(costs)
    avg = total / len(costs) if costs else 0
    threshold = avg * COST_ANOMALY_MULTIPLIER

    max_cost_exec = max(
        executions, key=lambda e: e.get("estimated_cost", 0) or 0
    ) if executions else None

    anomalies = [
        {
            "execution_id": e["id"],
            "cost": e.get("estimated_cost", 0),
            "avg_cost": round(avg, 6),
            "multiplier": round((e.get("estimated_cost", 0) or 0) / avg, 2) if avg > 0 else 0,
        }
        for e in executions
        if (e.get("estimated_cost", 0) or 0) > threshold
    ]

    trend: dict[str, float] = {}
    for e in executions:
        if e.get("started_at"):
            day = e["started_at"][:10]
            trend[day] = trend.get(day, 0) + (e.get("estimated_cost", 0) or 0)

    return {
        "total_cost": round(total, 6),
        "avg_cost_per_execution": round(avg, 6),
        "max_cost_execution": {
            "execution_id": max_cost_exec["id"],
            "cost": max_cost_exec.get("estimated_cost", 0),
        } if max_cost_exec else None,
        "cost_trend": [{"date": k, "cost": round(v, 6)} for k, v in sorted(trend.items())],
        "anomalies": anomalies[:20],
    }


@tool
def get_agent_info(agent_name: str) -> str:
    """Look up an agent by name. Returns agent details including id, model, owner, and status."""
    return f"AGENT_LOOKUP:{agent_name}"


@tool
def get_execution_logs(agent_id: str, start_date: str = "", end_date: str = "") -> str:
    """Retrieve execution logs for an agent within a date range. Returns execution records with status, latency, cost, and model info."""
    return f"EXECUTIONS:{agent_id}:{start_date}:{end_date}"


@tool
def get_execution_events(execution_ids: str) -> str:
    """Retrieve events for specific executions. Input is a comma-separated list of execution IDs. Returns event types, timestamps, and event data."""
    return f"EVENTS:{execution_ids}"


@tool
def analyze_failures_tool(execution_data: str) -> str:
    """Analyze failure patterns from execution data. Returns failure types, rates, common errors, and affected executions."""
    return f"FAILURES:{execution_data}"


@tool
def analyze_latency_tool(execution_data: str) -> str:
    """Analyze latency patterns including percentiles, spikes, and anomalies. Returns p50/p90/p99 latency and spike details."""
    return f"LATENCY:{execution_data}"


@tool
def analyze_costs_tool(execution_data: str) -> str:
    """Analyze cost patterns and detect cost anomalies. Returns total cost, average cost, cost trends, and anomalous executions."""
    return f"COSTS:{execution_data}"


def create_tools(session: AsyncSession):
    """Create tool functions bound to a database session."""

    async def resolve_agent(agent_name: str) -> Optional[dict[str, Any]]:
        return await _search_agent_by_name(session, agent_name)

    async def fetch_executions(
        agent_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        return await _get_executions(session, agent_id, start_date, end_date)

    async def fetch_events(execution_ids: list[str]) -> list[dict[str, Any]]:
        return await _get_events(session, execution_ids)

    def analyze_failures(executions: list[dict[str, Any]]) -> dict[str, Any]:
        return _analyze_failures(executions)

    def analyze_latency(executions: list[dict[str, Any]]) -> dict[str, Any]:
        return _analyze_latency(executions)

    def analyze_costs(executions: list[dict[str, Any]]) -> dict[str, Any]:
        return _analyze_costs(executions)

    def analyze_prompt_regressions(executions: list[dict[str, Any]]) -> dict[str, Any]:
        return _analyze_prompt_regressions(executions)

    async def get_agent(agent_id: str) -> Optional[dict[str, Any]]:
        return await _get_agent_info(session, agent_id)

    return {
        "resolve_agent": resolve_agent,
        "fetch_executions": fetch_executions,
        "fetch_events": fetch_events,
        "analyze_failures": analyze_failures,
        "analyze_latency": analyze_latency,
        "analyze_costs": analyze_costs,
        "analyze_prompt_regressions": analyze_prompt_regressions,
        "get_agent": get_agent,
    }