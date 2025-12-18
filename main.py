from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models, schemas, crud

# ================== APP INIT ==================
app = FastAPI(
    title="Smart Queue Backend",
    version="1.0.0"
)

# ================== SECURITY ==================
API_KEY = "SMARTQUEUE-ESP32-KEY"
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

# ================== CORS ==================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== DATABASE ==================
Base.metadata.create_all(bind=engine)

# ================== CONFIG ==================
CAPACITY_LIMIT = 10

# ================== ROOT ==================
@app.get("/")
def root():
    return {
        "status": "OK",
        "service": "Smart Queue Backend"
    }

# ================== EVENT ENDPOINT ==================
@app.post("/event", response_model=schemas.EventResponse)
def receive_event(
    event: schemas.EventIn,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
):
    """
    يستقبل حدث من ESP32:
    enter / exit
    """

    # 🔐 تحقق من API KEY
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    # 1️⃣ العدد الحالي
    current_count = crud.get_current_count(db, event.place_id)

    # 2️⃣ منطق الدخول
    if event.event == "enter":
        if current_count >= CAPACITY_LIMIT:
            return {
                "status": "FULL",
                "current_count": current_count,
                "message": "Capacity limit reached"
            }
        new_count = current_count + 1

    # 3️⃣ منطق الخروج
    elif event.event == "exit":
        new_count = max(0, current_count - 1)

    else:
        raise HTTPException(status_code=400, detail="Invalid event type")

    # 4️⃣ حفظ الحدث
    crud.create_event(
        db=db,
        place_id=event.place_id,
        event_type=event.event,
        event_time=event.time,
        current_count=new_count
    )

    # 5️⃣ الرد
    return {
        "status": "OK",
        "current_count": new_count,
        "message": "Event processed successfully"
    }

# ================== STATUS ENDPOINT ==================
@app.get("/status/{place_id}")
def get_status(
    place_id: str,
    db: Session = Depends(get_db)
):
    count = crud.get_current_count(db, place_id)

    return {
        "place_id": place_id,
        "current_count": count,
        "capacity": CAPACITY_LIMIT,
        "is_full": count >= CAPACITY_LIMIT
    }

# ================== EVENTS HISTORY ==================
@app.get("/events")
def get_events(
    place_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return crud.get_events(db, place_id, limit)
