import logging
import time
from typing import Any

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.nodes import (
    analyze_costs_node,
    analyze_failures_node,
    analyze_latency_node,
    analyze_prompt_regressions_node,
    fetch_events_node,
    fetch_executions_node,
    generate_report_node,
    resolve_agent_node,
)
from app.agents.state import InvestigatorState
from app.agents.tools import create_tools
from app.services.langfuse_service import langfuse_service

logger = logging.getLogger(__name__)


def build_graph(session: AsyncSession, trace_id: str | None = None) -> StateGraph:
    tools = create_tools(session)

    async def _track_node(node_name: str, state: InvestigatorState, func, config=None):
        """Track non-LLM pipeline steps as nested spans."""
        start_time = time.time()
        try:
            result = await func(state, config)
            latency_ms = int((time.time() - start_time) * 1000)

            if trace_id:
                try:
                    langfuse_service.track_investigation_node(
                        trace_id=trace_id,
                        node_name=node_name,
                        input_data={"query": state.get("query"), "agent_id": state.get("agent_id")},
                        output_data={
                            "keys": list(result.keys()) if isinstance(result, dict) else str(result)[:500]
                        },
                        latency_ms=latency_ms,
                    )
                except Exception as track_err:
                    logger.warning("Langfuse node tracking skipped (%s): %s", node_name, track_err)

            return result
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            if trace_id:
                try:
                    langfuse_service.track_investigation_node(
                        trace_id=trace_id,
                        node_name=node_name,
                        input_data={"query": state.get("query")},
                        output_data=None,
                        latency_ms=latency_ms,
                        error=str(e),
                    )
                except Exception as track_err:
                    logger.warning("Langfuse error tracking skipped (%s): %s", node_name, track_err)
            raise

    async def _resolve_agent(state: InvestigatorState, config=None) -> dict[str, Any]:
        state["_tools"] = tools
        return await _track_node("resolve_agent", state, resolve_agent_node, config)

    async def _fetch_executions(state: InvestigatorState, config=None) -> dict[str, Any]:
        return await _track_node("fetch_executions", state, fetch_executions_node, config)

    async def _fetch_events(state: InvestigatorState, config=None) -> dict[str, Any]:
        return await _track_node("fetch_events", state, fetch_events_node, config)

    async def _analyze_failures(state: InvestigatorState, config=None) -> dict[str, Any]:
        return await _track_node("analyze_failures", state, analyze_failures_node, config)

    async def _analyze_latency(state: InvestigatorState, config=None) -> dict[str, Any]:
        return await _track_node("analyze_latency", state, analyze_latency_node, config)

    async def _analyze_costs(state: InvestigatorState, config=None) -> dict[str, Any]:
        return await _track_node("analyze_costs", state, analyze_costs_node, config)

    async def _analyze_prompt_regressions(state: InvestigatorState, config=None) -> dict[str, Any]:
        return await _track_node("analyze_prompt_regressions", state, analyze_prompt_regressions_node, config)

    async def _generate_report(state: InvestigatorState, config=None) -> dict[str, Any]:
        return await _track_node("generate_report", state, generate_report_node, config)

    graph = StateGraph(InvestigatorState)

    graph.add_node("resolve_agent", _resolve_agent)
    graph.add_node("fetch_executions", _fetch_executions)
    graph.add_node("fetch_events", _fetch_events)
    graph.add_node("analyze_failures", _analyze_failures)
    graph.add_node("analyze_latency", _analyze_latency)
    graph.add_node("analyze_costs", _analyze_costs)
    graph.add_node("analyze_prompt_regressions", _analyze_prompt_regressions)
    graph.add_node("generate_report", _generate_report)

    graph.set_entry_point("resolve_agent")
    graph.add_edge("resolve_agent", "fetch_executions")
    graph.add_edge("fetch_executions", "fetch_events")
    graph.add_edge("fetch_events", "analyze_failures")
    graph.add_edge("analyze_failures", "analyze_latency")
    graph.add_edge("analyze_latency", "analyze_costs")
    graph.add_edge("analyze_costs", "analyze_prompt_regressions")
    graph.add_edge("analyze_prompt_regressions", "generate_report")
    graph.add_edge("generate_report", END)

    return graph.compile()


async def run_investigation(
    session: AsyncSession,
    query: str,
    agent_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    trace_id = langfuse_service.track_investigation_start(
        query=query,
        agent_id=agent_id,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
    )

    handler = langfuse_service.get_callback_handler(trace_id=trace_id)
    run_config: dict[str, Any] = {}
    if handler:
        run_config["callbacks"] = [handler]

    graph = build_graph(session, trace_id=trace_id)

    initial_state: InvestigatorState = {
        "query": query,
        "agent_id": agent_id,
        "start_date": start_date,
        "end_date": end_date,
    }

    logger.info("Starting investigation: query='%s', agent_id=%s", query, agent_id)

    try:
        final_state = await graph.ainvoke(initial_state, config=run_config)
        logger.info("Investigation complete")

        result = {
            "summary": final_state.get("report", ""),
            "confidence_score": final_state.get("confidence_score", 0.5),
            "root_causes": final_state.get("root_causes", []),
            "recommendations": final_state.get("recommendations", []),
            "report_source": final_state.get("report_source", "rule_based"),
            "agent_id": final_state.get("agent_id"),
            "query": query,
            "failure_analysis": final_state.get("failure_analysis"),
            "latency_analysis": final_state.get("latency_analysis"),
            "cost_analysis": final_state.get("cost_analysis"),
            "prompt_analysis": final_state.get("prompt_analysis"),
            "langfuse_trace_id": trace_id,
        }

        if trace_id:
            langfuse_service.track_investigation_end(
                trace_id=trace_id,
                summary=result["summary"],
                confidence_score=result["confidence_score"],
                root_causes=result["root_causes"],
                recommendations=result["recommendations"],
            )
            langfuse_service.flush()

        return result
    except Exception as e:
        logger.error("Investigation failed: %s", e)
        if trace_id:
            langfuse_service.update_trace(
                trace_id=trace_id,
                level="ERROR",
                status_message=f"Investigation failed: {str(e)}",
            )
            langfuse_service.flush()
        from app.agents.nodes import _rule_based_report

        fallback = _rule_based_report(initial_state)
        return {
            "summary": fallback["report"],
            "confidence_score": fallback["confidence_score"],
            "root_causes": fallback["root_causes"],
            "recommendations": fallback["recommendations"],
            "report_source": "rule_based",
            "agent_id": agent_id,
            "query": query,
            "langfuse_trace_id": trace_id,
        }
