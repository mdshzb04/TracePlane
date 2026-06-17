"""Compute production readiness from database and infrastructure checks."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limit import get_rate_limit_status
from app.models.agent import Agent
from app.models.api_key import ApiKey
from app.models.execution import Execution
from app.models.trace_span import TraceSpan
from app.models.user import User
from app.schemas.system import ProductionReadinessResponse, ReadinessCategory


class ReadinessService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _count(self, model) -> int:
        result = await self.session.execute(select(func.count()).select_from(model))
        return int(result.scalar() or 0)

    async def evaluate(
        self,
        *,
        redis_ok: bool,
        celery_worker_ok: bool | None,
        llm_configured: bool,
        env: str,
    ) -> ProductionReadinessResponse:
        agents = await self._count(Agent)
        executions = await self._count(Execution)
        spans = await self._count(TraceSpan)
        api_keys = await self._count(ApiKey)
        users = await self._count(User)

        categories: list[ReadinessCategory] = []

        sdk_score = 95 if api_keys > 0 else 40
        categories.append(
            ReadinessCategory(
                id="sdk_ingestion",
                name="SDK ingestion",
                score=sdk_score,
                status="ready" if executions > 0 else "partial",
                detail=f"{executions} executions ingested via API keys",
                missing_work=[] if executions > 0 else ["Send first SDK telemetry"],
            )
        )

        trace_score = 90 if spans > 0 else (50 if executions > 0 else 20)
        categories.append(
            ReadinessCategory(
                id="traces",
                name="Traces",
                score=trace_score,
                status="ready" if spans > 0 else "partial",
                detail=f"{spans} trace spans stored",
                missing_work=[] if spans > 0 else ["Ingest traces with span payloads"],
            )
        )

        exec_score = min(100, 60 + min(executions, 40))
        categories.append(
            ReadinessCategory(
                id="executions",
                name="Executions",
                score=exec_score,
                status="ready" if executions > 0 else "missing",
                detail=f"{executions} executions in database",
                missing_work=[] if executions > 0 else ["No execution data"],
            )
        )

        replay_missing = [] if llm_configured else ["Configure LLM provider for live replay"]
        categories.append(
            ReadinessCategory(
                id="replay",
                name="Replay",
                score=85 if llm_configured else 45,
                status="ready" if llm_configured else "partial",
                detail="Replay requires configured LLM — no echo fallback",
                missing_work=replay_missing,
            )
        )

        auth_score = 95 if users > 0 else 30
        auth_missing = []
        if env != "production":
            auth_missing.append("Set ENV=production before launch")
        if settings.SECRET_KEY.startswith("change-me"):
            auth_missing.append("Rotate SECRET_KEY from development default")
        categories.append(
            ReadinessCategory(
                id="auth",
                name="Auth",
                score=max(40, auth_score - len(auth_missing) * 15),
                status="ready" if not auth_missing else "partial",
                detail=f"{users} users; JWT + role-based access",
                missing_work=auth_missing,
            )
        )

        key_missing = []
        if api_keys == 0:
            key_missing.append("Create a Traceplane API key")
        categories.append(
            ReadinessCategory(
                id="api_keys",
                name="API keys",
                score=90 if api_keys > 0 else 35,
                status="ready" if api_keys > 0 else "missing",
                detail=f"{api_keys} API keys with request/cost tracking",
                missing_work=key_missing,
            )
        )

        rl = get_rate_limit_status()
        rl_missing = []
        if env == "production" and not rl["redis_available"]:
            rl_missing.append("Redis for distributed rate limiting")
        categories.append(
            ReadinessCategory(
                id="rate_limiting",
                name="Rate limiting",
                score=95 if rl["redis_available"] else (75 if env != "production" else 55),
                status="ready" if rl["redis_available"] else "partial",
                detail=f"Backend={rl['backend']}; protects auth and ingest",
                missing_work=rl_missing,
            )
        )

        mt_score = 85 if agents > 0 else 50
        mt_missing = []
        if not redis_ok:
            mt_missing.append("Redis for live WebSocket pub/sub")
        if settings.CELERY_ENABLED and not celery_worker_ok:
            mt_missing.append("Celery worker for async ingest")
        categories.append(
            ReadinessCategory(
                id="multi_tenancy",
                name="Multi-tenancy",
                score=max(50, mt_score - len(mt_missing) * 10),
                status="partial" if mt_missing else "ready",
                detail="Workspace-scoped agents and API keys",
                missing_work=mt_missing,
            )
        )

        overall = round(sum(c.score for c in categories) / len(categories))
        blockers = [w for c in categories for w in c.missing_work if c.status == "missing"]

        return ProductionReadinessResponse(
            overall_score=overall,
            categories=categories,
            blockers=blockers,
        )
