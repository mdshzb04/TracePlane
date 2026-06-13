import uuid
from typing import Optional

from fastapi import APIRouter, Query

from app.core.dependencies import DbSession, DeveloperUser
from app.schemas.evaluation_engine import (
    EvaluationDatasetCreate,
    EvaluationDatasetRead,
    EvaluationRunCreate,
    EvaluationRunRead,
    EvaluationScoreHistory,
)
from app.services.api_key_service import ApiKeyService
from app.services.evaluation_engine import EvaluationEngineService

router = APIRouter(prefix="/evaluation-engine", tags=["evaluation-engine"])


async def _workspace_id(user, db) -> uuid.UUID:
    service = ApiKeyService(db)
    return await service.ensure_user_workspace(user)


@router.get("/datasets", response_model=list[EvaluationDatasetRead])
async def list_datasets(user: DeveloperUser, db: DbSession):
    ws = await _workspace_id(user, db)
    return await EvaluationEngineService(db).list_datasets(ws)


@router.post("/datasets", response_model=EvaluationDatasetRead, status_code=201)
async def create_dataset(user: DeveloperUser, db: DbSession, data: EvaluationDatasetCreate):
    ws = await _workspace_id(user, db)
    return await EvaluationEngineService(db).create_dataset(ws, user.id, data)


@router.get("/datasets/{dataset_id}", response_model=EvaluationDatasetRead)
async def get_dataset(dataset_id: uuid.UUID, user: DeveloperUser, db: DbSession):
    ws = await _workspace_id(user, db)
    return await EvaluationEngineService(db).get_dataset(ws, dataset_id)


@router.post("/runs", response_model=EvaluationRunRead, status_code=201)
async def run_evaluation(user: DeveloperUser, db: DbSession, data: EvaluationRunCreate):
    ws = await _workspace_id(user, db)
    return await EvaluationEngineService(db).run_evaluation(ws, data)


@router.get("/runs", response_model=list[EvaluationRunRead])
async def list_runs(
    user: DeveloperUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
):
    ws = await _workspace_id(user, db)
    return await EvaluationEngineService(db).list_runs(ws, agent_id)


@router.get("/score-history", response_model=EvaluationScoreHistory)
async def score_history(
    user: DeveloperUser,
    db: DbSession,
    agent_id: Optional[uuid.UUID] = Query(default=None),
):
    ws = await _workspace_id(user, db)
    return await EvaluationEngineService(db).score_history(ws, agent_id)
