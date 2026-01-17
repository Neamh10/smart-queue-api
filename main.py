import os
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Security
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

Base.metadata.create_all(bind=engine)

# ======================
# Security
# ======================
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.environ.get("SMARTQUEUE_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="API KEY not configured"
        )

    if api_key != expected_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
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
    return {"status": "OK"}

# ======================
# EVENT
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
    result = crud.handle_event(
        db=db,
        place_id=event.place_id,
        event=event.event,
        time=event.time,
        capacity_limit=CAPACITY_LIMIT
    )

    await manager.broadcast(
        place_id=event.place_id,
        data={
            "place_id": event.place_id,
            "current_count": result["current_count"],
            "status": result["status"]
        }
    )

    return result

# ======================
# CONFIRM
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
        raise HTTPException(status_code=400, detail=status)

    return {"status": "CONFIRMED"}

# ======================
# RESERVATIONS
# ======================
@app.get(
    "/reservations",
    response_model=list[schemas.ReservationOut],
    dependencies=[Depends(verify_api_key)]
)
def list_reservations(db: Session = Depends(get_db)):
    crud.cleanup_expired_reservations(db)
    return crud.get_active_reservations(db)

# ======================
# WebSocket
# ======================
@app.websocket("/ws/{place_id}")
async def websocket_endpoint(websocket: WebSocket, place_id: str):
    await manager.connect(websocket, place_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, place_id)
