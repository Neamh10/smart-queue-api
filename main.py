from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import VisitEvent
from schemas import EventIn, EventResponse
from database import Base

# إنشاء الجداول
Base.metadata.create_all(bind=engine)

app = FastAPI()

# سعة المكان
CAPACITY_LIMIT = 50

# Dependency: DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- ENDPOINT ----------
@app.post("/event", response_model=EventResponse)
def receive_event(event: EventIn, db: Session = Depends(get_db)):

    if event.event not in ["enter", "exit"]:
        return {
            "status": "ERROR",
            "current_count": 0,
            "message": "Invalid event type"
        }

    # احسب العدد الحالي
    enters = db.query(VisitEvent).filter(
        VisitEvent.place_id == event.place_id,
        VisitEvent.event == "enter"
    ).count()

    exits = db.query(VisitEvent).filter(
        VisitEvent.place_id == event.place_id,
        VisitEvent.event == "exit"
    ).count()

    current_count = enters - exits

    # منع النزول تحت الصفر
    if event.event == "exit" and current_count <= 0:
        return {
            "status": "OK",
            "current_count": current_count,
            "message": "Exit ignored (count already zero)"
        }

    # حفظ الحدث
    new_event = VisitEvent(
        place_id=event.place_id,
        event=event.event,
        time=event.time
    )
    db.add(new_event)
    db.commit()

    # تحديث العدد
    current_count += 1 if event.event == "enter" else -1

    status = "FULL" if current_count >= CAPACITY_LIMIT else "OK"

    return {
        "status": status,
        "current_count": current_count,
        "message": "Event processed successfully"
    }
