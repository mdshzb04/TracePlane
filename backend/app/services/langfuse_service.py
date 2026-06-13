"""
Langfuse observability for AgentOps Hub (SDK v4).

Uses Langfuse Python SDK v4 best practices:
- get_client() singleton
- start_as_current_observation() for nested spans/generations
- propagate_attributes() for user_id, session_id, tags
- LangChain CallbackHandler for automatic LLM tracing
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Generator, Optional

from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

from app.core.config import settings

logger = logging.getLogger(__name__)

_MAX_IO_CHARS = 4000


def _truncate(value: Any, limit: int = _MAX_IO_CHARS) -> Any:
    if value is None:
        return None
    text = str(value)
    return text if len(text) <= limit else text[:limit] + "…"


def _string_metadata(data: dict[str, Any]) -> dict[str, str]:
    """Langfuse metadata values should be strings ≤200 chars."""
    result: dict[str, str] = {}
    for key, value in data.items():
        if value is None:
            continue
        text = str(value)
        result[key] = text[:200] if len(text) > 200 else text
    return result


class LangfuseService:
    """Centralized Langfuse tracing aligned with SDK v4 patterns."""

    def __init__(self) -> None:
        self._configured = False

    def _configure_env(self) -> None:
        """Sync settings into Langfuse env vars before get_client()."""
        if self._configured:
            return
        if settings.LANGFUSE_PUBLIC_KEY:
            os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
        if settings.LANGFUSE_SECRET_KEY:
            os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
        if settings.LANGFUSE_BASE_URL:
            os.environ["LANGFUSE_BASE_URL"] = settings.LANGFUSE_BASE_URL
        os.environ["LANGFUSE_TRACING_ENVIRONMENT"] = settings.LANGFUSE_TRACING_ENVIRONMENT
        self._configured = True

    @property
    def client(self):
        self._configure_env()
        return get_client()

    def is_enabled(self) -> bool:
        return bool(
            settings.LANGFUSE_ENABLED
            and settings.LANGFUSE_PUBLIC_KEY
            and settings.LANGFUSE_SECRET_KEY
        )

    def get_callback_handler(self, trace_id: Optional[str] = None) -> Optional[CallbackHandler]:
        """LangChain/LangGraph callback handler — auto-captures LLM calls."""
        if not self.is_enabled():
            return None
        trace_context = {"trace_id": trace_id} if trace_id else None
        return CallbackHandler(trace_context=trace_context)

    def create_trace_id(self, seed: Optional[str] = None) -> str:
        if not self.is_enabled():
            return ""
        return self.client.create_trace_id(seed=seed)

    @contextmanager
    def trace_context(
        self,
        *,
        name: str,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        input_data: Any = None,
        metadata: Optional[dict[str, Any]] = None,
        as_type: str = "span",
    ) -> Generator[Optional[Any], None, None]:
        """
        Root trace context with propagate_attributes for user/session/tags.

        Yields the root observation (or None when disabled).
        """
        if not self.is_enabled():
            yield None
            return

        resolved_trace_id = trace_id or self.client.create_trace_id()
        trace_ctx = {"trace_id": resolved_trace_id}
        meta = _string_metadata(metadata or {})

        propagate_kwargs: dict[str, Any] = {"tags": tags or []}
        if name:
            propagate_kwargs["trace_name"] = name
        if user_id:
            propagate_kwargs["user_id"] = str(user_id)
        if session_id:
            propagate_kwargs["session_id"] = str(session_id)

        try:
            with propagate_attributes(**propagate_kwargs):
                with self.client.start_as_current_observation(
                    as_type=as_type,  # type: ignore[arg-type]
                    name=name,
                    trace_context=trace_ctx,
                    input=_truncate(input_data),
                    metadata=meta,
                ) as root:
                    yield root
        except Exception as exc:
            logger.error("Langfuse trace context error: %s", exc)
            yield None

    @contextmanager
    def span_context(
        self,
        *,
        name: str,
        input_data: Any = None,
        metadata: Optional[dict[str, Any]] = None,
        as_type: str = "span",
    ) -> Generator[Optional[Any], None, None]:
        """Nested span within the current trace."""
        if not self.is_enabled():
            yield None
            return

        try:
            with self.client.start_as_current_observation(
                as_type=as_type,  # type: ignore[arg-type]
                name=name,
                input=_truncate(input_data),
                metadata=_string_metadata(metadata or {}),
            ) as span:
                yield span
        except Exception as exc:
            logger.error("Langfuse span error: %s", exc)
            yield None

    # -------------------------------------------------------------------------
    # Execution tracking
    # -------------------------------------------------------------------------

    def track_execution_start(
        self,
        execution_id: str,
        agent_id: str,
        agent_name: str,
        model: Optional[str],
        input_data: Optional[str],
        user_id: Optional[str] = None,
    ) -> Optional[str]:
        if not self.is_enabled():
            return None

        trace_id = self.client.create_trace_id(seed=execution_id)
        tags = ["execution", "agent", agent_name]
        if model:
            tags.append(model)

        metadata = _string_metadata({
            "execution_id": execution_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "model": model,
        })

        try:
            exec_attrs: dict[str, Any] = {
                "trace_name": f"execution:{agent_name}",
                "session_id": agent_id,
                "tags": tags,
            }
            if user_id:
                exec_attrs["user_id"] = str(user_id)
            with propagate_attributes(**exec_attrs):
                with self.client.start_as_current_observation(
                    as_type="span",
                    name=f"execution:{agent_name}",
                    trace_context={"trace_id": trace_id},
                    input=_truncate(input_data),
                    metadata=metadata,
                ):
                    pass
            return trace_id
        except Exception as exc:
            logger.error("Failed to track execution start: %s", exc)
            return None

    def track_execution_end(
        self,
        execution_id: str,
        output_data: Optional[str],
        status: str,
        latency_ms: Optional[int],
        token_usage: Optional[dict[str, int]],
        estimated_cost: Optional[float],
        model: Optional[str],
        error: Optional[str] = None,
    ) -> bool:
        if not self.is_enabled():
            return False

        trace_id = self.client.create_trace_id(seed=execution_id)
        level = "ERROR" if status == "failed" else "DEFAULT"

        metadata = _string_metadata({
            "status": status,
            "latency_ms": latency_ms,
            "estimated_cost": estimated_cost,
            "model": model,
            "token_usage": token_usage,
        })

        try:
            with self.client.start_as_current_observation(
                as_type="span",
                name="execution:complete",
                trace_context={"trace_id": trace_id},
                level=level,
                status_message=error or f"status={status}",
                metadata=metadata,
            ) as span:
                span.update(output=_truncate(output_data))
            return True
        except Exception as exc:
            logger.error("Failed to track execution end: %s", exc)
            return False

    def track_model_call(
        self,
        execution_id: str,
        model: str,
        input_data: Any,
        output_data: Any,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        latency_ms: int,
        model_parameters: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[str]:
        if not self.is_enabled():
            return None

        trace_id = self.client.create_trace_id(seed=execution_id)
        level = "ERROR" if error else "DEFAULT"

        try:
            with self.client.start_as_current_observation(
                as_type="generation",
                name=f"model:{model}",
                trace_context={"trace_id": trace_id},
                model=model,
                input=_truncate(input_data),
                level=level,
                status_message=error,
                model_parameters=model_parameters or {},
                usage_details={
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens,
                },
                cost_details={"total": cost},
            ) as generation:
                generation.update(output=_truncate(output_data))
            return trace_id
        except Exception as exc:
            logger.error("Failed to track model call: %s", exc)
            return None

    def track_tool_call(
        self,
        execution_id: str,
        tool_name: str,
        input_data: Any,
        output_data: Any,
        latency_ms: int,
        error: Optional[str] = None,
    ) -> Optional[str]:
        if not self.is_enabled():
            return None

        trace_id = self.client.create_trace_id(seed=execution_id)
        level = "ERROR" if error else "DEFAULT"

        try:
            with self.client.start_as_current_observation(
                as_type="tool",
                name=f"tool:{tool_name}",
                trace_context={"trace_id": trace_id},
                input=_truncate(input_data),
                level=level,
                status_message=error,
                metadata=_string_metadata({"latency_ms": latency_ms}),
            ) as tool_span:
                tool_span.update(output=_truncate(output_data))
            return trace_id
        except Exception as exc:
            logger.error("Failed to track tool call: %s", exc)
            return None

    # -------------------------------------------------------------------------
    # Evaluation tracking
    # -------------------------------------------------------------------------

    def track_evaluation(
        self,
        evaluation_id: str,
        agent_id: str,
        agent_name: str,
        test_case: str,
        expected_output: Optional[str],
        actual_output: Optional[str],
        score: Optional[float],
        user_id: Optional[str] = None,
    ) -> Optional[str]:
        if not self.is_enabled():
            return None

        trace_id = self.client.create_trace_id(seed=evaluation_id)

        try:
            eval_attrs: dict[str, Any] = {
                "trace_name": f"evaluation:{agent_name}",
                "session_id": f"eval-{agent_id}",
                "tags": ["evaluation", agent_name],
            }
            if user_id:
                eval_attrs["user_id"] = str(user_id)
            with propagate_attributes(**eval_attrs):
                with self.client.start_as_current_observation(
                    as_type="evaluator",
                    name=f"evaluation:{agent_name}",
                    trace_context={"trace_id": trace_id},
                    input=_truncate(test_case),
                    metadata=_string_metadata({
                        "evaluation_id": evaluation_id,
                        "agent_id": agent_id,
                        "score": score,
                    }),
                ) as evaluator:
                    evaluator.update(
                        output=_truncate(actual_output),
                        metadata=_string_metadata({
                            "expected_output": _truncate(expected_output),
                        }),
                    )
            return trace_id
        except Exception as exc:
            logger.error("Failed to track evaluation: %s", exc)
            return None

    # -------------------------------------------------------------------------
    # Investigator tracking
    # -------------------------------------------------------------------------

    def track_investigation_start(
        self,
        query: str,
        agent_id: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
        user_id: Optional[str] = None,
    ) -> Optional[str]:
        if not self.is_enabled():
            return None

        trace_id = self.client.create_trace_id()
        session_id = f"investigation-{agent_id}" if agent_id else "investigation-global"

        try:
            inv_attrs: dict[str, Any] = {
                "trace_name": "failure-investigation",
                "session_id": session_id,
                "tags": ["investigation", "failure-analysis"],
            }
            if user_id:
                inv_attrs["user_id"] = str(user_id)
            with propagate_attributes(**inv_attrs):
                with self.client.start_as_current_observation(
                    as_type="agent",
                    name="failure-investigation",
                    trace_context={"trace_id": trace_id},
                    input=_truncate(query),
                    metadata=_string_metadata({
                        "agent_id": agent_id,
                        "start_date": start_date,
                        "end_date": end_date,
                    }),
                ):
                    pass
            return trace_id
        except Exception as exc:
            logger.error("Failed to track investigation start: %s", exc)
            return None

    def track_investigation_node(
        self,
        trace_id: str,
        node_name: str,
        input_data: Any,
        output_data: Any,
        latency_ms: int,
        error: Optional[str] = None,
    ) -> Optional[str]:
        if not self.is_enabled() or not trace_id:
            return None

        level = "ERROR" if error else "DEFAULT"
        try:
            with self.client.start_as_current_observation(
                as_type="span",
                name=f"investigator:{node_name}",
                trace_context={"trace_id": trace_id},
                input=_truncate(input_data),
                level=level,
                status_message=error,
                metadata=_string_metadata({"latency_ms": latency_ms}),
            ) as span:
                span.update(output=_truncate(output_data))
            return trace_id
        except Exception as exc:
            logger.error("Failed to track investigation node: %s", exc)
            return None

    def track_investigation_end(
        self,
        trace_id: str,
        summary: str,
        confidence_score: float,
        root_causes: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
    ) -> bool:
        if not self.is_enabled() or not trace_id:
            return False

        try:
            with self.client.start_as_current_observation(
                as_type="span",
                name="investigator:report",
                trace_context={"trace_id": trace_id},
                metadata=_string_metadata({
                    "confidence_score": confidence_score,
                    "root_cause_count": len(root_causes),
                    "recommendation_count": len(recommendations),
                }),
            ) as span:
                span.update(output=_truncate(summary))
            return True
        except Exception as exc:
            logger.error("Failed to track investigation end: %s", exc)
            return False

    def update_trace(
        self,
        trace_id: str,
        output: Optional[Any] = None,
        level: Optional[str] = None,
        status_message: Optional[str] = None,
    ) -> bool:
        if not self.is_enabled() or not trace_id:
            return False

        try:
            with self.client.start_as_current_observation(
                as_type="span",
                name="trace-update",
                trace_context={"trace_id": trace_id},
                level=level,  # type: ignore[arg-type]
                status_message=status_message,
            ) as span:
                if output is not None:
                    span.update(output=_truncate(output))
            return True
        except Exception as exc:
            logger.error("Failed to update trace: %s", exc)
            return False

    # -------------------------------------------------------------------------
    # Analytics API (SDK v4 REST client)
    # -------------------------------------------------------------------------

    def fetch_traces(
        self,
        *,
        page: int = 1,
        limit: int = 20,
        tags: Optional[list[str]] = None,
        user_id: Optional[str] = None,
    ):
        tag_filter = tags[0] if tags else None
        return self.client.api.trace.list(
            page=page,
            limit=limit,
            tags=tag_filter,
            user_id=user_id,
        )

    def fetch_generations(self, *, limit: int = 1000):
        return self.client.api.observations.get_many(
            type="GENERATION",
            limit=limit,
        )

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def flush(self) -> bool:
        if not self.is_enabled():
            return False
        try:
            self.client.flush()
            return True
        except Exception as exc:
            logger.error("Langfuse flush failed: %s", exc)
            return False

    def shutdown(self) -> bool:
        if not self.is_enabled():
            return False
        try:
            self.client.shutdown()
            return True
        except Exception as exc:
            logger.error("Langfuse shutdown failed: %s", exc)
            return False


langfuse_service = LangfuseService()
