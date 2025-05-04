from fastapi import WebSocket
from typing import List
from ..config.globals import logger

# Store active WebSocket connections
active_websockets: List[WebSocket] = []


async def broadcast_log(message: str):
    """Broadcast a log message to all connected WebSocket clients"""
    logger.info(f"Broadcasting message: {message}")
    for websocket in active_websockets:
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error broadcasting to WebSocket: {e}")
            active_websockets.remove(websocket)
