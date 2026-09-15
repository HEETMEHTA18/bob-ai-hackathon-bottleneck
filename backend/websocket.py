import asyncio
import json
from datetime import datetime
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from backend.config import SECRET_KEY, ALGORITHM

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str, site_id: str):
        await websocket.accept()
        if site_id not in self.active_connections:
            self.active_connections[site_id] = set()
        self.active_connections[site_id].add(websocket)
        self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, user_id: str, site_id: str):
        if site_id in self.active_connections:
            self.active_connections[site_id].discard(websocket)
        self.user_connections.pop(user_id, None)

    async def broadcast_to_site(self, site_id: str, message: dict):
        if site_id in self.active_connections:
            dead = set()
            for conn in self.active_connections[site_id]:
                try:
                    await conn.send_json(message)
                except Exception:
                    dead.add(conn)
            self.active_connections[site_id] -= dead

    async def send_to_user(self, user_id: str, message: dict):
        conn = self.user_connections.get(user_id)
        if conn:
            try:
                await conn.send_json(message)
            except Exception:
                self.user_connections.pop(user_id, None)

manager = ConnectionManager()

async def verify_ws_token(token: str, site_id: str) -> str | None:
    """Validate WebSocket token and site ownership.

    Returns the user_id on success, or None if authentication/authorization
    fails.  site_id ownership is verified against the DB so users cannot
    subscribe to arbitrary sites.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

    # Must be an access token
    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    # Verify user exists, is active, and owns (or is admin for) the site.
    try:
        from backend.database import get_db
        from backend.models_db import User, Site
        from sqlalchemy import select
        async for db in get_db():
            result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
            user = result.scalar_one_or_none()
            if not user:
                return None

            # Admin users may subscribe to any site.
            if user.role == "admin":
                break

            # Non-admin: site must exist and belong to this user.
            site_result = await db.execute(
                select(Site).where(Site.id == site_id, Site.owner_id == user_id, Site.is_active == True)
            )
            if not site_result.scalar_one_or_none():
                return None
            break
    except Exception:
        return None

    return user_id

async def websocket_endpoint(websocket: WebSocket, token: str, site_id: str):
    user_id = await verify_ws_token(token, site_id)
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(websocket, user_id, site_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "subscribe_forecast":
                await manager.broadcast_to_site(site_id, {
                    "type": "forecast_update",
                    "data": {
                        "timestamp": datetime.now().isoformat(),
                        "site_id": site_id,
                    }
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, site_id)
