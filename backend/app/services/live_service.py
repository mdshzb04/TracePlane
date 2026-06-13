from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsParams,
    LiveDashboard,
    LiveExecutionSummary,
    LiveTopModel,
    LiveTopProvider,
)


class LiveService:
    def __init__(self, session: AsyncSession):
        self.repo = AnalyticsRepository(session)

    async def get_live_dashboard(self, params: AnalyticsParams) -> LiveDashboard:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_params = AnalyticsParams(
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=today_start,
        )

        recent = await self.repo.recent_executions(
            workspace_id=params.workspace_id,
            agent_id=params.agent_id,
            limit=15,
        )
        running = await self.repo.recent_executions(
            workspace_id=params.workspace_id,
            agent_id=params.agent_id,
            status="running",
            limit=10,
        )
        failed = await self.repo.recent_executions(
            workspace_id=params.workspace_id,
            agent_id=params.agent_id,
            status="failed",
            limit=10,
        )
        today_stats = await self.repo.execution_stats(
            agent_id=params.agent_id,
            workspace_id=params.workspace_id,
            start_date=today_start,
        )
        active_agents = await self.repo.count_active_agents(
            workspace_id=params.workspace_id,
            start_date=today_start,
        )
        top_providers = await self.repo.top_providers(
            workspace_id=params.workspace_id,
            agent_id=params.agent_id,
            start_date=today_start,
            limit=5,
        )
        top_models = await self.repo.top_models(
            workspace_id=params.workspace_id,
            agent_id=params.agent_id,
            start_date=today_start,
            limit=5,
        )

        total = today_stats["total"]
        success_rate = (today_stats["success"] / total * 100) if total > 0 else 0.0
        error_rate = (today_stats["failed"] / total * 100) if total > 0 else 0.0

        def _map(row: dict) -> LiveExecutionSummary:
            return LiveExecutionSummary(**row)

        return LiveDashboard(
            recent_executions=[_map(r) for r in recent],
            running_executions=[_map(r) for r in running],
            failed_executions=[_map(r) for r in failed],
            success_rate=round(success_rate, 2),
            error_rate=round(error_rate, 2),
            avg_latency_ms=round(today_stats["avg_latency_ms"], 1),
            executions_today=total,
            cost_today=round(today_stats["total_cost"], 6),
            tokens_today=today_stats["total_tokens"],
            input_tokens_today=today_stats["input_tokens"],
            output_tokens_today=today_stats["output_tokens"],
            active_agents=active_agents,
            top_providers=[
                LiveTopProvider(provider=row["provider"], request_count=row["request_count"])
                for row in top_providers
            ],
            top_models=[
                LiveTopModel(model=row["model"], request_count=row["request_count"])
                for row in top_models
            ],
        )
