from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends
from jose import JWTError, jwt
import asyncio
import json
import time

from utils.config import settings
from utils.logger import get_logger
from database.database import SessionLocal
from database.models import Document

logger = get_logger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Maps room_id -> {client_id: WebSocket}
        self.rooms: dict = {}

    async def connect(self, room_id: str, client_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][client_id] = websocket

    def disconnect(self, room_id: str, client_id: str):
        if room_id in self.rooms:
            self.rooms[room_id].pop(client_id, None)
            if not self.rooms[room_id]:
                self.rooms.pop(room_id, None)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast_to_room(self, room_id: str, message: dict):
        if room_id in self.rooms:
            for ws in list(self.rooms[room_id].values()):
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    async def broadcast_global(self, message: dict):
        for room_id, connections in list(self.rooms.items()):
            for ws in list(connections.values()):
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

# Throttling dictionary to prevent event flooding (10s cooldown per room and event text)
ALERT_COOLDOWNS = {}

def should_throttle_alert(room_id: str, title: str) -> bool:
    now = time.time()
    key = (room_id, title)
    last_sent = ALERT_COOLDOWNS.get(key, 0)
    if now - last_sent < 10.0:
        return True
    ALERT_COOLDOWNS[key] = now
    return False

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        return {"username": username, "role": role}
    except JWTError:
        return None

@router.websocket("/ws/ai/{document_id}")
async def websocket_ai_stream(websocket: WebSocket, document_id: str):
    token = websocket.query_params.get("token")
    user = verify_token(token) if token else None
    if not user:
        await websocket.accept()
        await manager.send_personal_message({"type": "error", "message": "Authentication required"}, websocket)
        await websocket.close(code=4003)
        return

    client_id = f"ai:{document_id}:{user['username']}"
    await manager.connect(document_id, client_id, websocket)
    logger.info(f"WS connected: {client_id}")
    try:
        init = await websocket.receive_json()
        message = init.get("message", "")

        from database.database import get_db_context
        with get_db_context() as db:
            doc = db.query(Document).filter(Document.id == document_id).first()

        if not doc:
            await manager.send_personal_message({"type": "error", "message": "document not found"}, websocket)
            return

        from services.chat_service import chat_with_document
        
        try:
            result = chat_with_document(document_id, message)
            reply = result.get("reply", "No distinct reply.")
            sources = result.get("sources", [])
            debug = result.get("debug", {})
            
            parts = reply.split()
            for i, p in enumerate(parts):
                await asyncio.sleep(0.04)
                await manager.send_personal_message({"type": "token", "data": p + " ", "index": i}, websocket)
                
            await manager.send_personal_message({
                "type": "done",
                "message": "complete",
                "sources": sources,
                "debug": debug,
                "grounded": result.get("grounded", True),
                "grounding_confidence": result.get("grounding_confidence", 0),
            }, websocket)

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            await manager.send_personal_message({"type": "error", "message": "Backend engine error"}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(document_id, client_id)
        logger.info(f"WS disconnected: {client_id}")

@router.websocket("/ws/alerts/{document_id}")
async def websocket_alerts(websocket: WebSocket, document_id: str):
    token = websocket.query_params.get("token")
    user = verify_token(token) if token else None
    if not user:
        await websocket.accept()
        await websocket.close(code=4003)
        return

    client_id = f"alerts:{user['username']}"
    await manager.connect(document_id, client_id, websocket)
    logger.info(f"Alerts WS connected to room {document_id}: {client_id}")
    try:
        while True:
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(document_id, client_id)
        logger.info(f"Alerts WS disconnected from room {document_id}: {client_id}")

@router.websocket("/ws/alerts")
async def websocket_alerts_legacy(websocket: WebSocket):
    """Fallback route to maintain backward compatibility for global/legacy connections."""
    token = websocket.query_params.get("token")
    user = verify_token(token) if token else None
    if not user:
        await websocket.accept()
        await websocket.close(code=4003)
        return

    client_id = f"alerts_legacy:{user['username']}"
    await manager.connect("GLOBAL", client_id, websocket)
    logger.info(f"Alerts WS connected legacy: {client_id}")
    try:
        while True:
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect("GLOBAL", client_id)
        logger.info(f"Alerts WS disconnected legacy: {client_id}")

@router.post("/notify")
async def notify(request: Request):
    payload = await request.json()
    await manager.broadcast_global(payload)
    return {"status": "broadcasted", "clients": sum(len(room) for room in manager.rooms.values())}

async def broadcast_alert(title: str, severity: str, document_id: str = None):
    msg = {"type": "alert", "title": title, "severity": severity, "message": title}
    if document_id:
        if should_throttle_alert(document_id, title):
            logger.info(f"Throttling duplicate alert for room {document_id}: {title}")
            return
        await manager.broadcast_to_room(document_id, msg)
        # Also broadcast to global channel for safety/dashboard-wide monitors
        await manager.broadcast_to_room("GLOBAL", msg)
    else:
        if should_throttle_alert("GLOBAL", title):
            logger.info(f"Throttling duplicate global alert: {title}")
            return
        await manager.broadcast_global(msg)
