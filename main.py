import os
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
# Security (API KEY)
# ======================
API_KEY = os.getenv("SMARTQUEUE_API_KEY", "DEV-KEY-CHANGE-ME")
print("API_KEY FROM ENV =", API_KEY)
api_key_header = APIKeyHeader(
    name="X-API-KEY",
    auto_error=False
)

def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


# ======================
# Config
# ======================
CAPACITY_LIMIT = 10
manager = ConnectionManager()


# ======================
# Middleware (CORS)
# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:5500"
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True
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
@app.post(
    "/event",
    response_model=schemas.EventResponse,
    dependencies=[Depends(verify_api_key)]
)
async def receive_event(
    event: schemas.EventIn,
    db: Session = Depends(get_db)
):
    # 1️⃣ Core Business Logic
    result = crud.handle_event(
        db=db,
        place_id=event.place_id,
        event=event.event,
        time=event.time,
        capacity_limit=CAPACITY_LIMIT
    )

    # 2️⃣ WebSocket Broadcast (Dashboard)
    await manager.broadcast(
        place_id=event.place_id,
        data={
            "place_id": event.place_id,
            "current_count": result["current_count"],
            "status": result["status"]
        }
    )

    # 3️⃣ Response to ESP32
    return result


# ======================
# CONFIRM RESERVATION
# ======================
@app.post(
    "/confirm",
    response_model=schemas.ConfirmReservationResponse,
    dependencies=[Depends(verify_api_key)]
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

    if status != "CONFIRMED":
        raise HTTPException(
            status_code=400,
            detail=status
        )

    return {
        "status": "CONFIRMED",
        "place_id": data.place_id
    }


# ======================
# RESERVATIONS (Dashboard)
# ======================
@app.get(
    "/reservations",
    response_model=list[schemas.ReservationOut],
    dependencies=[Depends(verify_api_key)]
)
def list_reservations(
    db: Session = Depends(get_db)
):
    crud.cleanup_expired_reservations(db)
    return crud.get_active_reservations(db)


# ======================
# WebSocket (Dashboard)
# ======================
@app.websocket("/ws/{place_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    place_id: str
):
    await manager.connect(websocket, place_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, place_id)


