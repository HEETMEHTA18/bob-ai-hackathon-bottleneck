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

async def verify_ws_token(token: str) -> str:
    """Validate WebSocket token with full security checks."""
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

    # Verify user exists and is active
    try:
        from backend.database import get_db
        from backend.models_db import User
        from sqlalchemy import select
        async for db in get_db():
            result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
            user = result.scalar_one_or_none()
            if not user:
                return None
            break
    except Exception:
        return None

    return user_id

async def websocket_endpoint(websocket: WebSocket, token: str, site_id: str):
    user_id = await verify_ws_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid or expired token")
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
