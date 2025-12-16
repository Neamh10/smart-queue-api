from fastapi import FastAPI, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from schemas import EventIn, EventResponse
from crud import handle_event, get_place

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Queue Backend")

API_KEY = "SMARTQUEUE-ESP32-KEY"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/event", response_model=EventResponse)
def receive_event(
    event: EventIn,
    db: Session = Depends(get_db),
    x_api_key: str = Header(None)
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    return handle_event(
        db=db,
        event_data=event
    )

@app.get("/sync")
def sync(place_id: str, db: Session = Depends(get_db)):
    place = get_place(db, place_id)
    return {
        "place_id": place.place_id,
        "count": place.current_count,
        "capacity": place.capacity,
        "status": "OK"
    }
