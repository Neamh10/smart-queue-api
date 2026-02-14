from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # place_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, place_id: str):
        await websocket.accept()
        self.active_connections.setdefault(place_id, []).append(websocket)
        print(f"📲 Device connected to {place_id}")

    def disconnect(self, websocket: WebSocket, place_id: str):
        if place_id in self.active_connections:
            if websocket in self.active_connections[place_id]:
                self.active_connections[place_id].remove(websocket)
                print(f"❌ Device disconnected from {place_id}")

            if not self.active_connections[place_id]:
                del self.active_connections[place_id]

    async def broadcast(self, place_id: str, data: dict):
        connections = self.active_connections.get(place_id, [])

        print(f"📡 Broadcasting to {place_id} ({len(connections)} devices)")

        for ws in connections:
            try:
                await ws.send_json(data)
            except:
                self.disconnect(ws, place_id)


# instance واحد يستخدم في المشروع كله
manager = ConnectionManager()
