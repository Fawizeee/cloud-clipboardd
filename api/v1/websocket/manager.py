"""
WebSocket Connection Manager
============================
Maintains a registry of active WebSocket connections keyed by user_id.
A single user may have multiple concurrent connections (one per device).
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, List

from fastapi import WebSocket


class ConnectionManager:
    """Thread-safe* WebSocket connection registry.

    *FastAPI/Starlette is async-only, so "thread-safe" here means we rely on
    the single-threaded asyncio event loop — no extra locking needed.
    """

    def __init__(self) -> None:
        # user_id -> list of active WebSocket connections
        self._connections: Dict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self._connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        sockets = self._connections.get(user_id, [])
        if websocket in sockets:
            sockets.remove(websocket)
        if not sockets:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: str, data: dict) -> None:
        """Broadcast a JSON payload to all connections belonging to user_id."""
        dead: List[WebSocket] = []
        for ws in list(self._connections.get(user_id, [])):
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, user_id)

    async def broadcast(self, data: dict) -> None:
        """Send a JSON payload to every connected client (all users)."""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, data)

    @property
    def active_connection_count(self) -> int:
        return sum(len(sockets) for sockets in self._connections.values())

    @property
    def active_user_count(self) -> int:
        return len(self._connections)


# Singleton instance shared across the application
manager = ConnectionManager()
