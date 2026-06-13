import asyncio
import logging
import uuid

from app.celery_app import celery_app
from app.database.session import async_session_factory
from app.schemas.ingest import IngestTraceRequest
from app.services.ingest import IngestService

logger = logging.getLogger(__name__)


@celery_app.task(name="ingest.process_trace", bind=True, max_retries=3)
def process_trace_task(self, payload: dict, workspace_id: str) -> dict:
    """Async background ingestion for high-volume SDK telemetry."""
    try:
        data = IngestTraceRequest.model_validate(payload)
        wid = uuid.UUID(workspace_id)
        result = asyncio.run(_ingest_async(data, wid))
        return result
    except Exception as exc:
        logger.exception("Ingest task failed (retry %s): %s", self.request.retries, exc)
        if self.request.retries >= self.max_retries:
            from app.tasks.dlq import ingest_dlq_task

            ingest_dlq_task.delay(payload, workspace_id, str(exc))
            raise
        raise self.retry(exc=exc, countdown=2 ** self.request.retries) from exc


async def _ingest_async(data: IngestTraceRequest, workspace_id: uuid.UUID) -> dict:
    async with async_session_factory() as session:
        service = IngestService(session)
        response = await service.ingest_trace(data, workspace_id=workspace_id)
        await session.commit()
        return response.model_dump(mode="json")
