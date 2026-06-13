import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.events import channel_for_workspace
from app.core.redis import get_redis
from app.core.ws_auth import authenticate_websocket
from app.database.session import async_session_factory

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

WS_CLOSE_UNAUTHORIZED = 4401


@router.websocket("/ws/live")
async def live_updates(websocket: WebSocket):
    async with async_session_factory() as session:
        auth = await authenticate_websocket(websocket, session)
        if auth is None:
            await websocket.close(code=WS_CLOSE_UNAUTHORIZED, reason="Unauthorized")
            return
        user, workspace_id = auth

    await websocket.accept()
    workspace_channel = channel_for_workspace(workspace_id)
    client = get_redis()

    if client is None:
        await websocket.send_json(
            {
                "type": "connected",
                "data": {
                    "mode": "polling_fallback",
                    "redis": False,
                    "workspace_id": str(workspace_id),
                },
            }
        )
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            return

    pubsub = client.pubsub()
    pubsub.subscribe(workspace_channel)

    async def _listen():
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("data"):
                try:
                    payload = json.loads(message["data"])
                    data = payload.get("data") or {}
                    # Belt-and-suspenders workspace isolation
                    if data.get("workspace_id") and str(data["workspace_id"]) != str(workspace_id):
                        continue
                    await websocket.send_json(payload)
                except Exception as exc:
                    logger.debug("WS send error: %s", exc)
            await asyncio.sleep(0.05)

    await websocket.send_json(
        {
            "type": "connected",
            "data": {
                "mode": "redis",
                "channel": workspace_channel,
                "workspace_id": str(workspace_id),
                "user_id": str(user.id),
            },
        }
    )
    task = asyncio.create_task(_listen())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        task.cancel()
        pubsub.unsubscribe(workspace_channel)
        pubsub.close()
