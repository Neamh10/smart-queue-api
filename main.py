from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models, schemas, crud

# ================== APP INIT ==================
app = FastAPI(
    title="Smart Queue Backend",
    version="1.0.0"
)

# ================== CORS ==================
# ضروري لـ ESP32 + Dashboard Web
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
CAPACITY_LIMIT = 10  # الحد الأقصى للمكان

# ================== ROOT ==================
@app.get("/")
def root():
    return {
        "status": "OK",
        "service": "Smart Queue Backend"
    }

# ================== EVENT ENDPOINT ==================
@app.post("/event", response_model=schemas.EventResponse)
def handle_event(
    event: schemas.EventIn,
    db: Session = Depends(get_db)
):
    """
    يستقبل حدث من ESP32:
    - enter
    - exit
    السيرفر يحسب العدد ويقرر FULL أو OK
    """

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
        raise HTTPException(
            status_code=400,
            detail="Invalid event type"
        )

    # 4️⃣ حفظ الحدث في قاعدة البيانات
    crud.create_event(
        db=db,
        place_id=event.place_id,
        event_type=event.event,
        event_time=event.time,
        current_count=new_count
    )

    # 5️⃣ الرد النهائي
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
    """
    Endpoint للـ Dashboard
    """
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
    """
    جلب سجل الأحداث (Dashboard / Analytics)
    """
    return crud.get_events(db, place_id, limit)
