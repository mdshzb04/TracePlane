"""Production readiness scoring from live system checks."""

from fastapi import APIRouter

from app.core.cache import cache_key, cached_async
from app.core.config import settings
from app.core.dependencies import DbSession, ViewerUser
from app.core.infrastructure import celery_worker_reachable, check_redis
from app.llm import get_llm_provider
from app.schemas.onboarding import OnboardingStatusResponse
from app.schemas.system import ProductionReadinessResponse
from app.services.onboarding import OnboardingService
from app.services.readiness import ReadinessService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/onboarding", response_model=OnboardingStatusResponse)
async def onboarding_status(current_user: ViewerUser, db: DbSession):
    key = cache_key("onboarding", str(current_user.id))

    async def _load():
        service = OnboardingService(db)
        return await service.get_status(current_user)

    return await cached_async(key, 300, _load)


@router.get("/readiness", response_model=ProductionReadinessResponse)
async def production_readiness(_: ViewerUser, db: DbSession):
    service = ReadinessService(db)
    return await service.evaluate(
        redis_ok=check_redis(),
        celery_worker_ok=celery_worker_reachable() if settings.CELERY_ENABLED else None,
        llm_configured=get_llm_provider().is_configured(),
        env=settings.ENV,
    )
