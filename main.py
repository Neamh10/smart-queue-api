from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import schemas, crud

app = FastAPI(title="Smart Queue Backend")

API_KEY = "SMARTQUEUE-ESP32-KEY"
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
CAPACITY_LIMIT = 10

@app.post("/event", response_model=schemas.EventResponse)
def receive_event(
    event: schemas.EventIn,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    return crud.handle_event(
        db=db,
        place_id=event.place_id,
        event=event.event,
        time=event.time,
        capacity_limit=CAPACITY_LIMIT
    )

@app.get("/status/{place_id}")
def get_status(place_id: str, db: Session = Depends(get_db)):
    count = crud.get_current_count(db, place_id)
    return {
        "place_id": place_id,
        "current_count": count
    }
