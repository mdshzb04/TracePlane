"""Dead-letter queue for failed Celery ingest tasks."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.core.infrastructure import get_redis

logger = logging.getLogger(__name__)

DLQ_KEY = "traceplane:ingest:dlq"


@celery_app.task(name="ingest.dlq", bind=True)
def ingest_dlq_task(self, payload: dict, workspace_id: str, error: str) -> dict:
    """Persist failed ingest payloads for manual replay."""
    entry = {
        "workspace_id": workspace_id,
        "error": error,
        "payload": payload,
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "task_id": self.request.id,
    }
    client = get_redis()
    if client is not None:
        try:
            client.lpush(DLQ_KEY, json.dumps(entry))
            client.ltrim(DLQ_KEY, 0, 999)
        except Exception as exc:
            logger.warning("DLQ Redis write failed: %s", exc)
    logger.error("Ingest moved to DLQ workspace=%s error=%s", workspace_id, error)
    return {"status": "dlq", "workspace_id": workspace_id}
