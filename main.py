from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import schemas, crud

app = FastAPI(
    title="Smart Queue Backend",
    version="1.0.0"
)

# 🔐 Security
API_KEY = "SMARTQUEUE-ESP32-KEY"
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

# 🌍 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🗄️ DB
Base.metadata.create_all(bind=engine)

CAPACITY_LIMIT = 10


@app.get("/")
def root():
    return {"status": "OK"}


@app.post("/event", response_model=schemas.EventResponse)
def receive_event(
    event: schemas.EventIn,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    status, count = crud.handle_event(
        db=db,
        place_id=event.place_id,
        event=event.event,
        event_id=event.event_id,
        time=event.time,
        capacity_limit=CAPACITY_LIMIT
    )

    return {
        "status": status,
        "current_count": count,
        "message": "Event processed"
    }


@app.get("/status/{place_id}")
def get_status(place_id: str, db: Session = Depends(get_db)):
    count = crud.get_current_count(db, place_id)
    return {
        "place_id": place_id,
        "current_count": count,
        "capacity": CAPACITY_LIMIT,
        "is_full": count >= CAPACITY_LIMIT
    }


@app.get("/events")
def events(place_id: str, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_events(db, place_id, limit)
