# app/api/routes/ws.py — WebSocket for real-time checklist updates
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json

router = APIRouter()

# Track active connections: { user_id: WebSocket }
active_connections: Dict[str, WebSocket] = {}

@router.websocket("/{user_id}")
async def checklist_ws(user_id: str, websocket: WebSocket):
    """
    Connect to receive live checklist updates.
    Frontend (Member 2) calls this to update the checklist dashboard in real time.
    """
    await websocket.accept()
    active_connections[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            # Echo back confirmation so UI can update optimistically
            await websocket.send_text(json.dumps({
                "type":    "checklist_update",
                "service": msg.get("service"),
                "step":    msg.get("step"),
                "status":  "received"
            }))
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)

async def broadcast_update(user_id: str, payload: dict):
    """
    Called by checklist route after DB update to push to connected client.
    """
    ws = active_connections.get(user_id)
    if ws:
        try:
            await ws.send_text(json.dumps({"type": "checklist_update", **payload}))
        except Exception:
            active_connections.pop(user_id, None)
