from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from datetime import datetime
from database import Base, engine, get_db
import schemas, crud
from manager import ConnectionManager

# ======================
# App Init
# ======================
app = FastAPI(title="Smart Queue Backend")

API_KEY = "SMARTQUEUE-ESP32-KEY"
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

manager = ConnectionManager()
CAPACITY_LIMIT = 10

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
# Static Frontend
# ======================
#app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

Base.metadata.create_all(bind=engine)

# ======================
# WebSocket
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
# REST API
# ======================
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
        time=event.time,
        capacity_limit=CAPACITY_LIMIT
    )

    # 🔥 بث لحظي للـ Dashboard
    await manager.broadcast({
        "place_id": event.place_id,
        "current_count": result["current_count"],
        "event": event.event,
        "time": datetime.utcnow().isoformat()
    })

    return result

# ======================
# Status
# ======================

@app.post("/event", response_model=schemas.EventResponse)
def receive_event(
    event: schemas.EventIn,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        return crud.handle_event(
            db=db,
            place_id=event.place_id,
            event=event.event,
            time=event.time
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
# ======================
# Events (Pagination)
# ======================
@app.get("/events/{place_id}", response_model=list[schemas.EventOut])
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


