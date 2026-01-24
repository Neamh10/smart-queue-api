from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, place_id: str):
        await websocket.accept()
        self.active_connections.setdefault(place_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, place_id: str):
        if place_id in self.active_connections:
            self.active_connections[place_id].remove(websocket)

    async def broadcast(self, place_id: str, data: dict):
        for ws in self.active_connections.get(place_id, []):
            await ws.send_json(data)
