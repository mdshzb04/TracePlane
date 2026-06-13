import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.evaluation import Evaluation
from app.repositories.agent import AgentRepository
from app.repositories.evaluation import EvaluationRepository
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationListParams,
    EvaluationRead,
    PaginatedEvaluationResponse,
)
from app.services.langfuse_service import langfuse_service

logger = logging.getLogger(__name__)


class EvaluationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = EvaluationRepository(session)
        self.agent_repo = AgentRepository(session)

    async def create_evaluation(
        self, data: EvaluationCreate, user_id: str | None = None
    ) -> EvaluationRead:
        agent = await self.agent_repo.get_by_id(data.agent_id)
        if agent is None:
            raise NotFoundError("Agent", str(data.agent_id))

        evaluation = Evaluation(
            agent_id=data.agent_id,
            test_case=data.test_case,
            expected_output=data.expected_output,
            actual_output=data.actual_output,
            score=data.score,
        )
        evaluation = await self.repo.create(evaluation)
        await self.session.flush()
        logger.info("Evaluation created: %s for agent %s", evaluation.id, evaluation.agent_id)

        langfuse_service.track_evaluation(
            evaluation_id=str(evaluation.id),
            agent_id=str(evaluation.agent_id),
            agent_name=agent.name,
            test_case=evaluation.test_case,
            expected_output=evaluation.expected_output,
            actual_output=evaluation.actual_output,
            score=float(evaluation.score) if evaluation.score else None,
            user_id=user_id,
        )

        return EvaluationRead.model_validate(evaluation)

    async def get_evaluation(self, evaluation_id: uuid.UUID) -> EvaluationRead:
        evaluation = await self.repo.get_by_id(evaluation_id)
        if evaluation is None:
            raise NotFoundError("Evaluation", str(evaluation_id))
        return EvaluationRead.model_validate(evaluation)

    async def list_evaluations(self, params: EvaluationListParams) -> PaginatedEvaluationResponse:
        import math

        offset = (params.page - 1) * params.page_size
        items, total = await self.repo.search(
            agent_id=params.agent_id,
            min_score=params.min_score,
            max_score=params.max_score,
            offset=offset,
            limit=params.page_size,
        )
        total_pages = math.ceil(total / params.page_size) if total > 0 else 1
        return PaginatedEvaluationResponse(
            items=[EvaluationRead.model_validate(e) for e in items],
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )
