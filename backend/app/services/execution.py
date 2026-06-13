import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.workspace_scope import get_agent_in_workspace, get_execution_in_workspace
from app.models.agent import Agent
from app.models.execution import Execution
from app.models.execution_event import ExecutionEvent
from app.repositories.agent import AgentRepository
from app.repositories.execution import ExecutionRepository
from app.repositories.execution_event import ExecutionEventRepository
from app.schemas.analytics import TraceEvent
from app.schemas.execution import (
    ExecutionCreate,
    ExecutionDetailRead,
    ExecutionEventCreate,
    ExecutionEventRead,
    ExecutionListParams,
    ExecutionRead,
    ExecutionSummary,
    ExecutionUpdate,
)
from app.services.langfuse_service import langfuse_service
from app.services.trace_explorer import TraceExplorerService, build_span_tree, build_timelines

logger = logging.getLogger(__name__)


class ExecutionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.exec_repo = ExecutionRepository(session)
        self.event_repo = ExecutionEventRepository(session)
        self.agent_repo = AgentRepository(session)

    async def _validate_agent(self, agent_id: uuid.UUID, workspace_id: uuid.UUID) -> Agent:
        return await get_agent_in_workspace(self.session, agent_id, workspace_id)

    async def create_execution(
        self, data: ExecutionCreate, workspace_id: uuid.UUID, user_id: str | None = None
    ) -> ExecutionRead:
        agent = await self._validate_agent(data.agent_id, workspace_id)
        execution = Execution(
            agent_id=data.agent_id,
            input=data.input,
            model=data.model,
            status="running",
            token_usage={},
            estimated_cost=0,
            started_at=datetime.now(timezone.utc),
        )
        execution = await self.exec_repo.create(execution)
        await self.session.flush()
        logger.info("Execution created: %s for agent %s", execution.id, execution.agent_id)

        langfuse_service.track_execution_start(
            execution_id=str(execution.id),
            agent_id=str(execution.agent_id),
            agent_name=agent.name if agent else "agent",
            model=execution.model,
            input_data=execution.input,
            user_id=user_id,
        )

        return ExecutionRead.model_validate(execution)

    async def get_execution(self, execution_id: uuid.UUID, workspace_id: uuid.UUID) -> ExecutionRead:
        execution = await get_execution_in_workspace(self.session, execution_id, workspace_id)
        return ExecutionRead.model_validate(execution)

    async def get_execution_detail(
        self, execution_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> ExecutionDetailRead:
        execution = await get_execution_in_workspace(self.session, execution_id, workspace_id)

        agent = await self.agent_repo.get_by_id(execution.agent_id)
        trace_svc = TraceExplorerService(self.session)
        spans_raw = await trace_svc.get_spans(execution_id)
        spans = build_span_tree(spans_raw)

        events_raw = await self.event_repo.get_by_execution_id(execution_id)
        trace_events = [
            TraceEvent(
                id=str(e.id),
                event_type=e.event_type,
                event_data=e.event_data or {},
                timestamp=e.timestamp.isoformat() if e.timestamp else "",
            )
            for e in events_raw
        ]
        timelines = build_timelines(trace_events)

        retry_count = sum(1 for e in events_raw if "retry" in e.event_type.lower())
        error_count = len(timelines.errors)

        base = ExecutionRead.model_validate(execution).model_dump()
        return ExecutionDetailRead(
            **base,
            agent_name=agent.name if agent else None,
            spans=spans,
            timelines=timelines,
            retry_count=retry_count,
            error_count=error_count,
        )

    async def list_executions(
        self, params: ExecutionListParams, workspace_id: uuid.UUID
    ) -> tuple[list[ExecutionRead], int, ExecutionSummary]:
        offset = (params.page - 1) * params.page_size
        filter_kwargs = dict(
            workspace_id=workspace_id,
            agent_id=params.agent_id,
            status=params.status,
            model=params.model,
            provider=params.provider,
            search=params.search,
            min_cost=params.min_cost,
            max_cost=params.max_cost,
            min_latency=params.min_latency,
            max_latency=params.max_latency,
            min_tokens=params.min_tokens,
        )
        rows, total = await self.exec_repo.search(
            **filter_kwargs,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            offset=offset,
            limit=params.page_size,
        )
        summary_data = await self.exec_repo.summary(**filter_kwargs)
        summary = ExecutionSummary(**summary_data)
        items = [
            ExecutionRead.model_validate(row[0]).model_copy(
                update={"agent_name": row[1], "provider": row[2]}
            )
            for row in rows
        ]
        return items, total, summary

    async def update_execution(
        self, execution_id: uuid.UUID, data: ExecutionUpdate, workspace_id: uuid.UUID
    ) -> ExecutionRead:
        execution = await get_execution_in_workspace(self.session, execution_id, workspace_id)
        updates = data.model_dump(exclude_unset=True)
        execution = await self.exec_repo.update(execution, updates)
        logger.info("Execution updated: %s → %s", execution.id, execution.status)

        langfuse_service.track_execution_end(
            execution_id=str(execution.id),
            output_data=execution.output,
            status=execution.status,
            latency_ms=execution.latency_ms,
            token_usage=execution.token_usage,
            estimated_cost=float(execution.estimated_cost) if execution.estimated_cost else None,
            model=execution.model,
            error=execution.output if execution.status == "failed" else None,
        )

        return ExecutionRead.model_validate(execution)

    async def add_event(
        self, execution_id: uuid.UUID, data: ExecutionEventCreate, workspace_id: uuid.UUID
    ) -> ExecutionEventRead:
        await get_execution_in_workspace(self.session, execution_id, workspace_id)
        event = ExecutionEvent(
            execution_id=execution_id,
            event_type=data.event_type,
            event_data=data.event_data or {},
        )
        event = await self.event_repo.create(event)
        await self.session.flush()
        logger.info("Execution event added: %s on %s", event.event_type, execution_id)
        return ExecutionEventRead.model_validate(event)

    async def get_events(
        self, execution_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> list[ExecutionEventRead]:
        await get_execution_in_workspace(self.session, execution_id, workspace_id)
        events = await self.event_repo.get_by_execution_id(execution_id)
        return [ExecutionEventRead.model_validate(e) for e in events]
