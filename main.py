from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from datetime import datetime

from database import Base, engine, get_db
import schemas, crud
from manager import ConnectionManager
from models import Place

# ======================
# App Init
# ======================
app = FastAPI(title="Smart Queue Backend")

# ======================
# Security
# ======================
API_KEY = "SMARTQUEUE-ESP32-KEY"
api_key_header = APIKeyHeader(
    name="X-API-KEY",
    auto_error=False
)

# ======================
# Config
# ======================
CAPACITY_LIMIT = 10
manager = ConnectionManager()

# ======================
# Middleware
# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# Database
# ======================
Base.metadata.create_all(bind=engine)

# ======================
# Root
# ======================
@app.get("/")
def root():
    return {
        "status": "OK",
        "service": "Smart Queue Backend"
    }

# ======================
# WebSocket (Dashboard)
# ======================
@app.websocket("/ws/{place_id}")
async def websocket_endpoint(websocket: WebSocket, place_id: str):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ======================
# EVENT (ESP32 → Server)
# ======================
@app.post("/event", response_model=schemas.EventResponse)
async def receive_event(
    event: schemas.EventIn,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        result = crud.handle_event(
            db=db,
            place_id=event.place_id,
            event=event.event,
            time=event.time,
            capacity_limit=CAPACITY_LIMIT
        )
    except Exception as e:
        print("HANDLE_EVENT ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

    await manager.broadcast({
        "place_id": event.place_id,
        "current_count": result["current_count"],
        "event": event.event,
        "time": datetime.utcnow().isoformat()
    })

    return result

    #  Broadcast realtime update
    await manager.broadcast({
        "place_id": event.place_id,
        "current_count": result["current_count"],
        "event": event.event,
        "time": datetime.utcnow().isoformat()
    })

    return result

# ======================
# SYNC (ESP32 startup)
# ======================
@app.get("/sync")
def sync_place(
    place_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    place = (
        db.query(Place)
        .filter(Place.place_id == place_id)
        .first()
    )

    return {
        "place_id": place_id,
        "current_count": place.current_count if place else 0,
        "capacity": CAPACITY_LIMIT
    }

# ======================
# EVENTS HISTORY
# ======================
@app.get(
    "/events/{place_id}",
    response_model=list[schemas.EventOut]
)
def get_events(
    place_id: str,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    events = crud.get_events_paginated(
        db=db,
        place_id=place_id,
        page=page,
        page_size=page_size
    )

    events.reverse()
    return events

    # Broadcast Real-Time
    await manager.broadcast(result["payload"])

    return result

