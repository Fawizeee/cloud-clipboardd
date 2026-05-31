"""
WebSocket Route
===============
WS /api/v1/ws?token=<access_token>

Clients authenticate via query-parameter token (Bearer header is not available
over native WebSocket). Once connected they can send event messages and receive
real-time clipboard updates broadcast by the server.

Supported client → server events
---------------------------------
clipboard_update  — client pushed a new clipboard item
sync_request      — client wants items since a given timestamp

Server → client events
-----------------------
connected             — connection confirmation with device_id
clipboard_updated     — a new/updated item from another device
sync_response         — response to a sync_request
error                 — error feedback for a bad message
"""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session

from api.v1.websocket.manager import manager
from core.security import decode_token
from db.session import get_db
from db.models.user import User
from db.models.clipboard import ClipboardItem
from services.clipboard_service import create_clipboard_item
from schemas.clipboard import SaveClipboardRequest

router = APIRouter(tags=["websocket"])


def _get_user_from_token(token: str, db: Session) -> User | None:
    """Validate a JWT access token and return the corresponding User, or None."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return (
        db.query(User)
        .filter(User.id == user_id, User.is_deleted == False)  # noqa: E712
        .first()
    )


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token for authentication"),
    db: Session = Depends(get_db),
):
    """
    Authenticated WebSocket endpoint.

    The client connects with ?token=<access_token> in the query string.
    After JWT validation the connection is accepted and the user is registered
    in the ConnectionManager so the server can push real-time events to all
    of their active devices.
    """
    user = _get_user_from_token(token, db)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized: invalid or expired token")
        return

    user_id = str(user.id)
    await manager.connect(websocket, user_id)

    # Confirm connection
    await websocket.send_text(
        json.dumps({
            "event": "connected",
            "data": {
                "user_id": user_id,
                "message": "WebSocket connection established",
                "server_time": datetime.utcnow().isoformat(),
                "active_connections": manager.active_connection_count,
            },
        })
    )

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"event": "error", "data": {"message": "Invalid JSON"}})
                )
                continue

            event = message.get("event")
            data = message.get("data", {})

            # ── clipboard_update ─────────────────────────────────────────────
            if event == "clipboard_update":
                content = data.get("content", "")
                content_type = data.get("content_type", "text")
                source_device_name = data.get("source_device_name")

                try:
                    req = SaveClipboardRequest(
                        content=content,
                        content_type=content_type,
                        source_device_name=source_device_name,
                    )
                    saved = await create_clipboard_item(db, user, req)

                    # Broadcast to all of the user's other connected devices
                    await manager.send_to_user(
                        user_id,
                        {
                            "event": "clipboard_updated",
                            "data": {
                                "id": saved.id,
                                "content": saved.content,
                                "content_type": saved.content_type,
                                "source_device_name": source_device_name,
                                "created_at": saved.created_at.isoformat(),
                            },
                        },
                    )
                except Exception as exc:
                    await websocket.send_text(
                        json.dumps({"event": "error", "data": {"message": str(exc)}})
                    )

            # ── sync_request ─────────────────────────────────────────────────
            elif event == "sync_request":
                last_sync_raw = data.get("last_sync_timestamp")
                try:
                    last_sync = (
                        datetime.fromisoformat(last_sync_raw)
                        if last_sync_raw
                        else datetime.utcfromtimestamp(0)
                    )
                except (ValueError, TypeError):
                    last_sync = datetime.utcfromtimestamp(0)

                items = (
                    db.query(ClipboardItem)
                    .filter(
                        ClipboardItem.user_id == user.id,
                        ClipboardItem.updated_at > last_sync,
                        ClipboardItem.is_deleted == False,  # noqa: E712
                    )
                    .order_by(ClipboardItem.updated_at.asc())
                    .limit(100)
                    .all()
                )

                sync_items = [
                    {
                        "id": str(i.id),
                        "content": i.content,
                        "content_type": i.content_type,
                        "created_at": i.created_at.isoformat(),
                        "updated_at": i.updated_at.isoformat(),
                    }
                    for i in items
                ]

                await websocket.send_text(
                    json.dumps({
                        "event": "sync_response",
                        "data": {
                            "items": sync_items,
                            "sync_timestamp": datetime.utcnow().isoformat(),
                        },
                    })
                )

            # ── unknown event ─────────────────────────────────────────────────
            else:
                await websocket.send_text(
                    json.dumps({
                        "event": "error",
                        "data": {"message": f"Unknown event type: '{event}'"},
                    })
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
