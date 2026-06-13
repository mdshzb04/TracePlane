import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import publish_event
from app.llm.pricing import estimate_cost
from app.models.agent import Agent
from app.models.execution import Execution
from app.models.execution_event import ExecutionEvent
from app.repositories.execution import ExecutionRepository
from app.repositories.execution_event import ExecutionEventRepository
from app.schemas.ingest import DiscoveryInfo, IngestTraceRequest, IngestTraceResponse
from app.services.agent_discovery import discover_agent_meta
from app.services.agent_observability import AgentObservabilityService
from app.services.api_key_service import ApiKeyService
from app.services.langfuse_service import langfuse_service
from app.services.span_builder import SpanBuilder

logger = logging.getLogger(__name__)


class IngestService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.exec_repo = ExecutionRepository(session)
        self.event_repo = ExecutionEventRepository(session)

    async def ingest_trace(
        self,
        data: IngestTraceRequest,
        workspace_id: uuid.UUID,
        api_key_id: uuid.UUID | None = None,
    ) -> IngestTraceResponse:
        discovered = discover_agent_meta(data)
        agent, created_agent = await self._upsert_agent(data, workspace_id, discovered)
        now = datetime.now(timezone.utc)

        token_usage = data.token_usage or {}
        input_tokens = int(token_usage.get("input_tokens", 0) or 0)
        output_tokens = int(token_usage.get("output_tokens", 0) or 0)
        model = discovered.model if discovered.model != "unknown" else (data.model or agent.model or "unknown")
        cost = data.estimated_cost
        if cost is None and (input_tokens or output_tokens):
            cost = estimate_cost(model, input_tokens, output_tokens)

        status = data.status
        if status == "running":
            status = "success"

        execution = Execution(
            agent_id=agent.id,
            input=data.input,
            output=data.output,
            status=status,
            latency_ms=data.latency_ms,
            model=model,
            token_usage=token_usage,
            estimated_cost=cost or 0,
            started_at=now,
            completed_at=now if status != "running" else None,
        )
        execution = await self.exec_repo.create(execution)
        await self.session.flush()

        if created_agent:
            await self._emit(
                execution.id,
                "agent.discovered",
                {
                    "agent_id": str(agent.id),
                    "agent_name": agent.external_name or agent.name,
                    "framework": agent.framework,
                    "model": agent.model,
                    "provider": agent.provider,
                    "source": "sdk",
                },
            )

        if not data.events:
            await self._emit(execution.id, "execution.started", {"agent": agent.external_name, "trace_id": data.trace_id})
            if data.input:
                await self._emit(execution.id, "input.received", {"preview": data.input[:500]})
            if "input_tokens" in token_usage or "output_tokens" in token_usage:
                await self._emit(
                    execution.id,
                    "model.call.completed",
                    {"model": model, **token_usage, "latency_ms": data.latency_ms},
                )
            if data.output:
                await self._emit(execution.id, "output.generated", {"preview": data.output[:500]})
            await self._emit(execution.id, "execution.completed", {"status": status})
        else:
            for event in data.events:
                ev = ExecutionEvent(
                    execution_id=execution.id,
                    event_type=event.event_type,
                    event_data=event.event_data or {},
                    timestamp=event.timestamp or now,
                )
                await self.event_repo.create(ev)
            await self.session.flush()

        await self._persist_spans(execution.id, data, agent.external_name or agent.name, model, now)

        langfuse_service.track_execution_start(
            execution_id=str(execution.id),
            agent_id=str(agent.id),
            agent_name=agent.name,
            model=model,
            input_data=data.input,
            user_id=str(workspace_id),
        )
        langfuse_service.track_execution_end(
            execution_id=str(execution.id),
            output_data=data.output,
            status=status,
            latency_ms=data.latency_ms,
            token_usage=token_usage,
            estimated_cost=float(cost) if cost else None,
            model=model,
            error=data.output if status == "failed" else None,
        )

        health = await AgentObservabilityService(self.session).get_agent_health(agent.id)

        publish_event(
            "execution.ingested",
            {
                "execution_id": str(execution.id),
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "status": status,
                "latency_ms": data.latency_ms,
                "estimated_cost": float(cost or 0),
                "workspace_id": str(workspace_id),
                "health_score": health.health_score,
            },
            workspace_id=workspace_id,
        )
        if created_agent:
            publish_event(
                "agent.discovered",
                {
                    "agent_id": str(agent.id),
                    "agent_name": agent.name,
                    "framework": agent.framework,
                    "model": agent.model,
                    "provider": agent.provider,
                    "health_score": health.health_score,
                    "execution_id": str(execution.id),
                    "workspace_id": str(workspace_id),
                },
                workspace_id=workspace_id,
            )

        if api_key_id:
            from app.repositories.api_key import ApiKeyRepository

            key_repo = ApiKeyRepository(self.session)
            api_key = await key_repo.get_by_id(api_key_id)
            if api_key:
                await ApiKeyService(self.session).record_usage(api_key, float(cost or 0))

        try:
            from app.services.alert_service import AlertService

            await AlertService(self.session).evaluate_on_ingest(workspace_id)
        except Exception:
            logger.exception("Alert evaluation failed after ingest workspace=%s", workspace_id)

        logger.info(
            "Ingested trace: agent=%s execution=%s created_agent=%s health=%.1f",
            agent.id,
            execution.id,
            created_agent,
            health.health_score,
        )
        return IngestTraceResponse(
            agent_id=agent.id,
            execution_id=execution.id,
            trace_id=execution.id,
            created_agent=created_agent,
            health_score=health.health_score,
            discovery=DiscoveryInfo(
                framework=agent.framework or discovered.framework,
                model=agent.model or model,
                provider=agent.provider or discovered.provider,
            ),
        )

    async def _persist_spans(
        self,
        execution_id: uuid.UUID,
        data: IngestTraceRequest,
        agent_name: str,
        model: str,
        base_time: datetime,
    ) -> None:
        builder = SpanBuilder(execution_id, base_time)
        spans = []
        if data.spans:
            spans = builder.from_explicit_spans(data.spans)
        elif data.events:
            spans = builder.from_events(data.events)
        else:
            spans = [builder.default_root(agent_name, model)]

        for span in spans:
            self.session.add(span)
        await self.session.flush()

    async def _upsert_agent(
        self,
        data: IngestTraceRequest,
        workspace_id: uuid.UUID,
        discovered,
    ) -> tuple[Agent, bool]:
        meta = data.agent
        external_name = meta.name.strip()
        now = datetime.now(timezone.utc)
        framework = meta.framework or discovered.framework
        model = meta.model or (discovered.model if discovered.model != "unknown" else None)
        provider = meta.provider or discovered.provider

        stmt = select(Agent).where(
            and_(Agent.workspace_id == workspace_id, Agent.external_name == external_name)
        )
        result = await self.session.execute(stmt)
        agent = result.scalar_one_or_none()

        if agent:
            agent.model = model or agent.model
            agent.framework = framework or agent.framework
            agent.provider = provider or agent.provider
            agent.environment = meta.environment or agent.environment
            agent.owner = meta.owner or agent.owner
            if meta.tags:
                agent.tags = list({*(agent.tags or []), *meta.tags})
            agent.last_seen_at = now
            agent.status = "active"
            await self.session.flush()
            return agent, False

        tags = list({*(meta.tags or []), "auto-discovered"})
        agent = Agent(
            name=external_name,
            external_name=external_name,
            description=f"Auto-discovered via SDK ({framework})",
            owner=meta.owner or "sdk",
            model=model,
            framework=framework,
            provider=provider,
            environment=meta.environment or "production",
            tags=tags,
            source="sdk",
            status="active",
            workspace_id=workspace_id,
            last_seen_at=now,
        )
        self.session.add(agent)
        await self.session.flush()
        return agent, True

    async def _emit(self, execution_id: uuid.UUID, event_type: str, event_data: dict) -> None:
        event = ExecutionEvent(
            execution_id=execution_id,
            event_type=event_type,
            event_data=event_data,
        )
        await self.event_repo.create(event)
