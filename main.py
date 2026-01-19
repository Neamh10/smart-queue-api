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

from database import Base, engine, get_db
import crud
import schemas
from manager import ConnectionManager

# ======================
# App Init
# ======================
app = FastAPI(title="Smart Queue Backend")

# Create DB tables
Base.metadata.create_all(bind=engine)

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
# Root
# ======================
@app.get("/")
def root():
    return {
        "status": "OK",
        "service": "Smart Queue Backend"
    }

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

    # Core Logic
    result = crud.handle_event(
        db=db,
        place_id=event.place_id,
        event=event.event,
        time=event.time,
        capacity_limit=CAPACITY_LIMIT
    )

    # WebSocket Broadcast 
    await manager.broadcast(
        place_id=event.place_id,
        data={
            "place_id": event.place_id,
            "current_count": result["current_count"],
            "status": result["status"]
        }
    )

    # HTTP Response للـ ESP32
    return result

# ======================
# CONFIRM RESERVATION
# ======================
@app.post(
    "/confirm",
    response_model=schemas.ConfirmReservationResponse
)
def confirm_reservation(
    data: schemas.ConfirmReservationIn,
    db: Session = Depends(get_db)
):
    reservation, status = crud.confirm_reservation(
        db=db,
        token=data.token,
        place_id=data.place_id
    )

if status in ["INVALID", "WRONG_PLACE", "EXPIRED"]:
    raise HTTPException(
        status_code=400,
        detail=status
    )

# ENTERED = نجاح
return {
    "status": status,   # ENTERED
    "place_id": data.place_id
}


@app.get(
    "/reservations",
    response_model=list[schemas.ReservationOut]
)
def list_reservations(
    db: Session = Depends(get_db)
):
    reservations = crud.get_active_reservations(db)
    return reservations


# ======================
# WebSocket (Dashboard)
# ======================
@app.websocket("/ws/{place_id}")
async def websocket_endpoint(websocket: WebSocket, place_id: str):
    await manager.connect(websocket, place_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, place_id)


