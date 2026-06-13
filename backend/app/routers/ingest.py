import logging

from fastapi import APIRouter

from app.core.config import settings
from app.core.dependencies import DbSession, IngestAuth
from app.core.infrastructure import celery_worker_reachable
from app.schemas.ingest import IngestTraceRequest, IngestTraceResponse
from app.services.ingest import IngestService
from app.services.otel_ingest import otel_resource_spans_to_ingest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/trace", response_model=IngestTraceResponse, status_code=201)
async def ingest_trace(
    data: IngestTraceRequest,
    ctx: IngestAuth,
    db: DbSession,
):
    """SDK telemetry ingestion — auto-discovers agents and records executions."""
    if settings.CELERY_ENABLED and celery_worker_reachable():
        try:
            from app.tasks.ingest import process_trace_task

            task = process_trace_task.delay(
                data.model_dump(mode="json"),
                str(ctx.workspace_id),
            )
            result = task.get(timeout=60)
            return IngestTraceResponse.model_validate(result)
        except Exception as exc:
            logger.warning("Celery ingest failed, using sync fallback: %s", exc)

    service = IngestService(db)
    result = await service.ingest_trace(
        data,
        workspace_id=ctx.workspace_id,
        api_key_id=ctx.api_key.id,
    )
    return result


@router.post("/otel", response_model=IngestTraceResponse, status_code=201)
async def ingest_otel_trace(
    payload: dict,
    ctx: IngestAuth,
    db: DbSession,
):
    """Ingest OpenTelemetry OTLP/JSON traces."""
    data = otel_resource_spans_to_ingest(payload)
    service = IngestService(db)
    return await service.ingest_trace(
        data,
        workspace_id=ctx.workspace_id,
        api_key_id=ctx.api_key.id,
    )
