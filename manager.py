from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, place_id: str):
        await websocket.accept()
        self.active_connections.setdefault(place_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, place_id: str):
        self.active_connections[place_id].remove(websocket)

    async def broadcast(self, place_id: str, data: dict):
        for ws in self.active_connections.get(place_id, []):
            await ws.send_json(data)
