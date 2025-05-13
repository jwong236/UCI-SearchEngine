from fastapi import WebSocket
from typing import List
from ..config.globals import logger
import json
from datetime import datetime

active_websockets: List[WebSocket] = []
message_counter = 0
last_broadcast_messages = set()


async def broadcast_log(message: str):
    """
    Broadcast a log message to all connected WebSocket clients
    with rate limiting to prevent flooding
    """
    global message_counter, last_broadcast_messages

    logger.info(f"Broadcasting: {message}")

    message_counter += 1
    if message_counter > 100:
        message_counter = 0
        last_broadcast_messages.clear()

    timestamp = datetime.now().isoformat()
    payload = json.dumps({"message": message, "timestamp": timestamp})

    disconnected_sockets = []
    for websocket in active_websockets:
        try:
            await websocket.send_text(payload)
        except Exception as e:
            disconnected_sockets.append(websocket)

    for socket in disconnected_sockets:
        if socket in active_websockets:
            active_websockets.remove(socket)
