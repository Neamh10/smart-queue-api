import os
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import crud
import schemas
from manager import ConnectionManager

app = FastAPI(title="Smart Queue Backend")

Base.metadata.create_all(bind=engine)

# ======================
# Security
# ======================
api_key_header = APIKeyHeader(name="X-API-KEY")

def verify_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.getenv("SMARTQUEUE_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=500, detail="API KEY not configured")
    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# ======================
CAPACITY_LIMIT = 10
manager = ConnectionManager()

# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

@app.get("/")
def root():
    return {"status": "OK"}

@app.post("/event", response_model=schemas.EventResponse, dependencies=[Depends(verify_api_key)])
async def receive_event(event: schemas.EventIn, db: Session = Depends(get_db)):
    result = crud.handle_event(
        db=db,
        place_id=event.place_id,
        event=event.event,
        time=event.time,
        capacity_limit=CAPACITY_LIMIT
    )

    await manager.broadcast(event.place_id, result)
    return result

@app.post("/confirm", response_model=schemas.ConfirmReservationResponse, dependencies=[Depends(verify_api_key)])
def confirm_reservation(data: schemas.ConfirmReservationIn, db: Session = Depends(get_db)):
    _, status = crud.confirm_reservation(db, data.token, data.place_id)
    if status != "CONFIRMED":
        raise HTTPException(status_code=400, detail=status)
    return {"status": "CONFIRMED", "place_id": data.place_id}

@app.get("/reservations", response_model=list[schemas.ReservationOut], dependencies=[Depends(verify_api_key)])
def reservations(db: Session = Depends(get_db)):
    return crud.get_active_reservations(db)

@app.websocket("/ws/{place_id}")
async def websocket_endpoint(ws: WebSocket, place_id: str):
    await manager.connect(ws, place_id)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws, place_id)

@app.get("/debug-env")
def debug_env():
    return {
        "SMARTQUEUE_API_KEY": os.getenv("SMARTQUEUE_API_KEY")
    }
