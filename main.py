from fastapi import FastAPI, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal, engine
import models
from schemas import EventIn, EventResponse
from crud import handle_event, get_place
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-KEY")


# إنشاء الجداول
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Queue Backend")

# ================== CONFIG ==================
API_KEY = "SMARTQUEUE-ESP32-KEY"

# ================== DB DEPENDENCY ==================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================== EVENT ENDPOINT ==================
api_key_header = APIKeyHeader(name="X-API-KEY")
@app.post("/event", response_model=EventResponse)
def receive_event(
    event: EventIn,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    return handle_event(
        db=db,
        place_id=event.place_id,
        event=event.event,
        event_id=event.event_id,
        time=event.time
    )

# ================== SYNC ENDPOINT ==================
@app.get("/sync")
def sync(place_id: str, db: Session = Depends(get_db)):
    place = get_place(db, place_id)

    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    return {
        "place_id": place.place_id,
        "count": place.current_count,
        "capacity": place.capacity,
        "status": "OK"
    }

# ================== HEALTH CHECK ==================
@app.get("/")
def health():
    return {"status": "Smart Queue Backend is running"}


