from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # { "hall_1": [ws1, ws2], "hall_2": [ws3] }
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, place_id: str):
        await websocket.accept()
        if place_id not in self.active_connections:
            self.active_connections[place_id] = []
        self.active_connections[place_id].append(websocket)

    def disconnect(self, websocket: WebSocket, place_id: str):
        if place_id in self.active_connections:
            self.active_connections[place_id].remove(websocket)

    async def broadcast(self, place_id: str, data: dict):
        if place_id not in self.active_connections:
            return

        for websocket in self.active_connections[place_id]:
            await websocket.send_json(data)

def update_place_state(place):
    if place.current_count >= place.capacity:
        place.state = "FULL"
    else:
        place.state = "NORMAL"
