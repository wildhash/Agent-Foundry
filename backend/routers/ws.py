"""
WebSocket support for real-time pipeline updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for pipeline updates"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, pipeline_id: str):
        await websocket.accept()
        if pipeline_id not in self.active_connections:
            self.active_connections[pipeline_id] = set()
        self.active_connections[pipeline_id].add(websocket)
        logger.info(f"WebSocket connected for pipeline {pipeline_id}")

    def disconnect(self, websocket: WebSocket, pipeline_id: str):
        if pipeline_id in self.active_connections:
            self.active_connections[pipeline_id].discard(websocket)
            if not self.active_connections[pipeline_id]:
                del self.active_connections[pipeline_id]

    async def broadcast(self, pipeline_id: str, message: dict):
        """Broadcast message to all connections for a pipeline"""
        if pipeline_id not in self.active_connections:
            return

        dead_connections = set()
        for connection in self.active_connections[pipeline_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)

        # Clean up dead connections
        for dead in dead_connections:
            self.active_connections[pipeline_id].discard(dead)


manager = ConnectionManager()


@router.websocket("/pipeline/{pipeline_id}")
async def pipeline_websocket(websocket: WebSocket, pipeline_id: str):
    """WebSocket endpoint for pipeline status updates"""
    await manager.connect(websocket, pipeline_id)
    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await websocket.receive_text()
            # Could handle client commands here if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, pipeline_id)


# Helper function for emitting events from orchestrator
async def emit_pipeline_event(pipeline_id: str, event_type: str, data: dict):
    """Emit event to all connected clients for a pipeline"""
    message = {
        "type": event_type,
        "pipeline_id": pipeline_id,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    }
    await manager.broadcast(pipeline_id, message)
