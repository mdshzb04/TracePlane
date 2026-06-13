import json
import logging
import uuid
from typing import Any

from app.core.redis import get_redis

logger = logging.getLogger(__name__)

CHANNEL_PREFIX = "agentops:live"
# Legacy global channel — do not subscribe in production WS handler
CHANNEL = f"{CHANNEL_PREFIX}:global"


def channel_for_workspace(workspace_id: uuid.UUID | str) -> str:
    return f"{CHANNEL_PREFIX}:{workspace_id}"


def publish_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    workspace_id: uuid.UUID | str | None = None,
) -> None:
    client = get_redis()
    if client is None:
        return
    ws_id = payload.get("workspace_id") or workspace_id
    if ws_id is None:
        logger.warning("publish_event %s skipped: missing workspace_id", event_type)
        return
    channel = channel_for_workspace(ws_id)
    try:
        client.publish(channel, json.dumps({"type": event_type, "data": payload}))
    except Exception as exc:
        logger.warning("Failed to publish event %s: %s", event_type, exc)
