import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import InvestigatorState
from app.llm import get_llm_provider

logger = logging.getLogger(__name__)


async def resolve_agent_node(state: InvestigatorState, config=None) -> dict[str, Any]:
    """Resolve agent name from query or use provided agent_id."""
    tools = state.get("_tools")
    if not tools:
        return {"agent_info": None}

    agent_id = state.get("agent_id")
    query = state.get("query", "")

    if agent_id:
        agent_info = await tools["get_agent"](agent_id)
        if agent_info:
            logger.info("Resolved agent by ID: %s", agent_info["name"])
            return {"agent_info": agent_info, "agent_id": agent_info["id"]}

    provider = get_llm_provider()
    extraction_prompt = f"""Extract the agent name from this query. Return ONLY the agent name, nothing else.
If no specific agent is mentioned, return "all".

Query: {query}
Agent name:"""

    response = await provider.invoke([HumanMessage(content=extraction_prompt)], config=config)
    agent_name = response.content.strip().strip('"').strip("'")

    if agent_name.lower() == "all":
        logger.info("Query targets all agents")
        return {"agent_info": None}

    agent_info = await tools["resolve_agent"](agent_name)
    if agent_info:
        logger.info("Resolved agent by name: %s → %s", agent_name, agent_info["id"])
        return {"agent_info": agent_info, "agent_id": agent_info["id"]}

    logger.warning("Could not resolve agent: %s", agent_name)
    return {"agent_info": None}


async def fetch_executions_node(state: InvestigatorState, config=None) -> dict[str, Any]:
    """Fetch execution logs for the resolved agent."""
    tools = state.get("_tools")
    if not tools:
        return {"executions": []}

    agent_id = state.get("agent_id")
    start_date = state.get("start_date")
    end_date = state.get("end_date")

    executions = await tools["fetch_executions"](
        agent_id=agent_id,
        start_date=start_date,
        end_date=end_date,
    )
    logger.info("Fetched %d executions for agent %s", len(executions), agent_id)
    return {"executions": executions}


async def fetch_events_node(state: InvestigatorState, config=None) -> dict[str, Any]:
    """Fetch execution events for the retrieved executions."""
    tools = state.get("_tools")
    if not tools:
        return {"events": []}

    executions = state.get("executions", [])
    if not executions:
        return {"events": []}

    execution_ids = [e["id"] for e in executions[:50]]
    events = await tools["fetch_events"](execution_ids)
    logger.info("Fetched %d events for %d executions", len(events), len(execution_ids))
    return {"events": events}


async def analyze_failures_node(state: InvestigatorState, config=None) -> dict[str, Any]:
    """Analyze failure patterns from execution data."""
    tools = state.get("_tools")
    if not tools:
        return {"failure_analysis": None}

    executions = state.get("executions", [])
    failure_analysis = tools["analyze_failures"](executions)
    logger.info(
        "Failure analysis: %d failures (%.1f%% failure rate)",
        failure_analysis["total_failures"],
        failure_analysis["failure_rate"],
    )
    return {"failure_analysis": failure_analysis}


async def analyze_latency_node(state: InvestigatorState, config=None) -> dict[str, Any]:
    """Analyze latency patterns."""
    tools = state.get("_tools")
    if not tools:
        return {"latency_analysis": None}

    executions = state.get("executions", [])
    latency_analysis = tools["analyze_latency"](executions)
    logger.info(
        "Latency analysis: avg=%.0fms, p99=%.0fms, %d spikes",
        latency_analysis["avg_latency_ms"],
        latency_analysis["p99_latency_ms"],
        latency_analysis["spike_count"],
    )
    return {"latency_analysis": latency_analysis}


async def analyze_costs_node(state: InvestigatorState, config=None) -> dict[str, Any]:
    """Analyze cost patterns."""
    tools = state.get("_tools")
    if not tools:
        return {"cost_analysis": None}

    executions = state.get("executions", [])
    cost_analysis = tools["analyze_costs"](executions)
    logger.info(
        "Cost analysis: total=$%.4f, avg=$%.6f, %d anomalies",
        cost_analysis["total_cost"],
        cost_analysis["avg_cost_per_execution"],
        len(cost_analysis["anomalies"]),
    )
    return {"cost_analysis": cost_analysis}


async def analyze_prompt_regressions_node(state: InvestigatorState, config=None) -> dict[str, Any]:
    """Detect prompt version regressions across executions."""
    tools = state.get("_tools")
    if not tools:
        return {"prompt_analysis": None}

    executions = state.get("executions", [])
    prompt_analysis = tools["analyze_prompt_regressions"](executions)
    logger.info(
        "Prompt regression analysis: %d regressions detected",
        prompt_analysis.get("regression_count", 0),
    )
    return {"prompt_analysis": prompt_analysis}


def _rule_based_report(state: InvestigatorState) -> dict[str, Any]:
    """DB-backed investigation report when LLM is unavailable."""
    query = state.get("query", "")
    agent_info = state.get("agent_info") or {}
    failure_analysis = state.get("failure_analysis") or {}
    latency_analysis = state.get("latency_analysis") or {}
    cost_analysis = state.get("cost_analysis") or {}
    executions = state.get("executions", [])
    failed = [e for e in executions if e.get("status") == "failed"]

    root_causes: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []

    if failure_analysis.get("total_failures", 0) > 0:
        rate = failure_analysis.get("failure_rate", 0)
        root_causes.append(
            {
                "category": "error_pattern",
                "description": f"{failure_analysis['total_failures']} failed executions ({rate:.1f}% failure rate).",
                "evidence": [e.get("output", "")[:200] for e in failed[:3] if e.get("output")],
                "severity": "high" if rate > 20 else "medium",
            }
        )
        recommendations.append(
            {
                "title": "Review failed execution outputs",
                "description": "Inspect trace explorer for failed runs and correlate error events.",
                "priority": "high",
            }
        )

    if latency_analysis.get("spike_count", 0) > 0:
        root_causes.append(
            {
                "category": "latency_spike",
                "description": f"{latency_analysis['spike_count']} latency spikes detected (p99={latency_analysis.get('p99_latency_ms', 0):.0f}ms).",
                "evidence": [],
                "severity": "medium",
            }
        )

    if cost_analysis.get("anomalies"):
        root_causes.append(
            {
                "category": "cost_spike",
                "description": f"{len(cost_analysis['anomalies'])} cost anomalies vs average.",
                "evidence": [],
                "severity": "medium",
            }
        )

    agent_name = agent_info.get("name", "the agent")
    summary = (
        f"Analysis of {len(executions)} executions for {agent_name}: "
        f"{failure_analysis.get('total_failures', 0)} failures, "
        f"avg latency {latency_analysis.get('avg_latency_ms', 0):.0f}ms. "
        f"Query: {query}"
    )
    confidence = 0.75 if root_causes else 0.5

    return {
        "report": summary,
        "confidence_score": confidence,
        "root_causes": root_causes,
        "recommendations": recommendations or [
            {
                "title": "Continue monitoring",
                "description": "No critical patterns detected in stored execution data.",
                "priority": "low",
            }
        ],
    }


async def generate_report_node(state: InvestigatorState, config=None) -> dict[str, Any]:
    """Generate the investigation report using the LLM (Investigator V2)."""
    provider = get_llm_provider()

    query = state.get("query", "")
    agent_info = state.get("agent_info")
    executions = state.get("executions", [])
    events = state.get("events", [])
    failure_analysis = state.get("failure_analysis")
    latency_analysis = state.get("latency_analysis")
    cost_analysis = state.get("cost_analysis")
    prompt_analysis = state.get("prompt_analysis")

    context = {
        "query": query,
        "agent": agent_info,
        "executions_summary": {
            "total": len(executions),
            "statuses": {},
        },
        "failure_analysis": failure_analysis,
        "latency_analysis": latency_analysis,
        "cost_analysis": cost_analysis,
        "prompt_analysis": prompt_analysis,
        "events_sample": events[:20],
        "failed_executions_sample": [
            {
                "id": e["id"],
                "status": e["status"],
                "latency_ms": e.get("latency_ms"),
                "estimated_cost": e.get("estimated_cost"),
                "output": (e.get("output") or "")[:300],
                "started_at": e.get("started_at"),
            }
            for e in executions
            if e.get("status") == "failed"
        ][:10],
        "high_latency_sample": [
            {
                "id": e["id"],
                "latency_ms": e.get("latency_ms"),
                "started_at": e.get("started_at"),
            }
            for e in executions
            if e.get("latency_ms") and e["latency_ms"] > 5000
        ][:10],
    }

    for e in executions:
        status = e.get("status", "unknown")
        context["executions_summary"]["statuses"][status] = (
            context["executions_summary"]["statuses"].get(status, 0) + 1
        )

    system_prompt = """You are an AI Agent Failure Investigator V2. You analyze execution logs, events, failure patterns, latency spikes, cost spikes, prompt regressions, and error patterns to produce investigation reports.

Given the analysis data, produce a structured JSON response with:
1. "summary" - A concise 2-4 sentence summary of findings
2. "confidence_score" - A float between 0 and 1 representing confidence in the analysis
3. "root_causes" - A list of root causes, each with:
   - "category": one of "timeout", "rate_limit", "context_overflow", "network_error", "auth_error", "validation_error", "cost_spike", "latency_spike", "prompt_regression", "error_pattern", "configuration", "resource_exhaustion", "unknown"
   - "description": detailed explanation
   - "evidence": list of specific evidence strings
   - "severity": one of "low", "medium", "high", "critical"
4. "recommendations" - A list of actionable recommendations, each with:
   - "title": short title
   - "description": detailed recommendation
   - "priority": one of "low", "medium", "high", "critical"

Respond ONLY with valid JSON. No markdown, no explanation outside the JSON."""

    user_prompt = f"""Investigation data:

{json.dumps(context, indent=2, default=str)}

Produce the investigation report as JSON."""

    if not provider.is_configured():
        logger.warning("LLM not configured — using rule-based investigation report")
        fallback = _rule_based_report(state)
        fallback["report_source"] = "rule_based"
        return fallback

    llm_config = None
    if config and isinstance(config, dict):
        llm_config = {k: v for k, v in config.items() if k != "callbacks"}

    try:
        response = await provider.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ],
            config=llm_config,
        )
    except Exception as exc:
        logger.warning("LLM investigation failed, using rule-based fallback: %s", exc)
        fallback = _rule_based_report(state)
        fallback["report_source"] = "rule_based"
        return fallback

    raw = response.content.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        report_data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM response as JSON: %s", raw[:500])
        report_data = {
            "summary": raw[:500],
            "confidence_score": 0.3,
            "root_causes": [],
            "recommendations": [],
        }

    return {
        "report": report_data.get("summary", ""),
        "confidence_score": report_data.get("confidence_score", 0.5),
        "root_causes": report_data.get("root_causes", []),
        "recommendations": report_data.get("recommendations", []),
        "report_source": "llm",
    }