import logging
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.evaluation import Evaluation
from app.models.evaluation_dataset import EvaluationDataset, EvaluationRun
from app.models.execution import Execution
from app.repositories.agent import AgentRepository
from app.schemas.evaluation_engine import (
    EvaluationDatasetCreate,
    EvaluationDatasetRead,
    EvaluationRunCreate,
    EvaluationRunRead,
    EvaluationRunResult,
    EvaluationScoreHistory,
)

logger = logging.getLogger(__name__)


def _score_output(expected: str | None, actual: str | None) -> float:
    if not expected or not actual:
        return 1.0 if actual else 0.0
    return round(SequenceMatcher(None, expected.strip(), actual.strip()).ratio(), 4)


class EvaluationEngineService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.agent_repo = AgentRepository(session)

    async def create_dataset(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID, data: EvaluationDatasetCreate
    ) -> EvaluationDatasetRead:
        dataset = EvaluationDataset(
            workspace_id=workspace_id,
            name=data.name,
            description=data.description,
            items=[item.model_dump() for item in data.items],
            created_by=user_id,
        )
        self.session.add(dataset)
        await self.session.flush()
        return EvaluationDatasetRead.model_validate(dataset)

    async def list_datasets(self, workspace_id: uuid.UUID) -> list[EvaluationDatasetRead]:
        stmt = (
            select(EvaluationDataset)
            .where(EvaluationDataset.workspace_id == workspace_id)
            .order_by(EvaluationDataset.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [EvaluationDatasetRead.model_validate(d) for d in result.scalars().all()]

    async def get_dataset(self, workspace_id: uuid.UUID, dataset_id: uuid.UUID) -> EvaluationDatasetRead:
        dataset = await self._get_dataset(workspace_id, dataset_id)
        return EvaluationDatasetRead.model_validate(dataset)

    async def run_evaluation(
        self, workspace_id: uuid.UUID, data: EvaluationRunCreate
    ) -> EvaluationRunRead:
        dataset = await self._get_dataset(workspace_id, data.dataset_id)
        agent = await self.agent_repo.get_by_id(data.agent_id)
        if agent is None or agent.workspace_id != workspace_id:
            raise NotFoundError("Agent", str(data.agent_id))

        run = EvaluationRun(
            dataset_id=dataset.id,
            agent_id=data.agent_id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        await self.session.flush()

        results: list[EvaluationRunResult] = []
        scores: list[float] = []

        for item in dataset.items or []:
            test_case = item.get("test_case", "")
            expected = item.get("expected_output")
            actual = await self._latest_output_for_agent(data.agent_id, test_case)
            score = _score_output(expected, actual)
            scores.append(score)

            evaluation = Evaluation(
                agent_id=data.agent_id,
                test_case=test_case,
                expected_output=expected,
                actual_output=actual,
                score=score,
                evaluation_date=datetime.now(timezone.utc),
            )
            self.session.add(evaluation)
            await self.session.flush()

            results.append(
                EvaluationRunResult(
                    test_case=test_case,
                    expected_output=expected,
                    actual_output=actual,
                    score=score,
                    evaluation_id=str(evaluation.id),
                )
            )

        run.status = "completed"
        run.average_score = round(sum(scores) / len(scores), 4) if scores else 0.0
        run.results = [r.model_dump() for r in results]
        run.completed_at = datetime.now(timezone.utc)
        await self.session.flush()

        logger.info("Evaluation run %s completed: avg=%.2f", run.id, run.average_score or 0)
        return EvaluationRunRead.model_validate(run)

    async def list_runs(
        self, workspace_id: uuid.UUID, agent_id: uuid.UUID | None = None
    ) -> list[EvaluationRunRead]:
        stmt = (
            select(EvaluationRun)
            .join(EvaluationDataset, EvaluationDataset.id == EvaluationRun.dataset_id)
            .where(EvaluationDataset.workspace_id == workspace_id)
        )
        if agent_id:
            stmt = stmt.where(EvaluationRun.agent_id == agent_id)
        stmt = stmt.order_by(EvaluationRun.created_at.desc())
        result = await self.session.execute(stmt)
        return [EvaluationRunRead.model_validate(r) for r in result.scalars().all()]

    async def score_history(
        self, workspace_id: uuid.UUID, agent_id: uuid.UUID | None = None
    ) -> EvaluationScoreHistory:
        stmt = (
            select(EvaluationRun)
            .join(EvaluationDataset, EvaluationDataset.id == EvaluationRun.dataset_id)
            .where(
                EvaluationDataset.workspace_id == workspace_id,
                EvaluationRun.status == "completed",
            )
        )
        if agent_id:
            stmt = stmt.where(EvaluationRun.agent_id == agent_id)
        stmt = stmt.order_by(EvaluationRun.completed_at.asc())
        result = await self.session.execute(stmt)
        points = [
            {
                "date": r.completed_at.isoformat() if r.completed_at else "",
                "average_score": r.average_score,
                "run_id": str(r.id),
                "agent_id": str(r.agent_id),
            }
            for r in result.scalars().all()
        ]
        return EvaluationScoreHistory(points=points)

    async def _get_dataset(self, workspace_id: uuid.UUID, dataset_id: uuid.UUID) -> EvaluationDataset:
        stmt = select(EvaluationDataset).where(
            EvaluationDataset.id == dataset_id,
            EvaluationDataset.workspace_id == workspace_id,
        )
        result = await self.session.execute(stmt)
        dataset = result.scalar_one_or_none()
        if dataset is None:
            raise NotFoundError("EvaluationDataset", str(dataset_id))
        return dataset

    async def _latest_output_for_agent(self, agent_id: uuid.UUID, test_case: str) -> str | None:
        pattern = f"%{test_case[:80]}%"
        stmt = (
            select(Execution.output)
            .where(Execution.agent_id == agent_id, Execution.input.ilike(pattern))
            .order_by(Execution.started_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar()
