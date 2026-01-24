from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import crud
from manager import ConnectionManager
import schemas

app = FastAPI(title="Smart Queue Backend")

Base.metadata.create_all(bind=engine)

API_KEY = "SMARTQUEUE-ESP32-KEY"
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

CAPACITY_LIMIT = 10
manager = ConnectionManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "OK", "service": "Smart Queue Backend"}


@app.post("/event", response_model=schemas.EventResponse)
async def receive_event(
    event: schemas.EventIn,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    result = crud.handle_event(
        db=db,
        place_id=event.place_id,
        event=event.event,
        capacity_limit=CAPACITY_LIMIT
    )

  await manager.broadcast(
    place_id=event.place_id,
    data={
        "place_id": event.place_id,
        "state": result["state"],
        "current_count": result["current_count"],
        "portal_url": result.get("portal_url")
    }
)


    return result


@app.websocket("/ws/{place_id}")
async def websocket_endpoint(websocket: WebSocket, place_id: str):
    await manager.connect(websocket, place_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, place_id)

