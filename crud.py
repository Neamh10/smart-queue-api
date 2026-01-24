from sqlalchemy.orm import Session
from datetime import datetime
from models import Place, VisitEvent


def get_or_create_place(db: Session, place_id: str, capacity: int):
    place = db.query(Place).filter_by(id=place_id).first()
    if not place:
        place = Place(
            id=place_id,
            capacity=capacity,
            current_count=0,
            state="NORMAL"
        )
        db.add(place)
        db.commit()
        db.refresh(place)
    return place


def update_place_state(place: Place):
    place.state = "FULL" if place.current_count >= place.capacity else "NORMAL"


def log_event(db: Session, place_id: str, event: str, count: int):
    log = VisitEvent(
        place_id=place_id,
        event=event,
        current_count=count
    )
    db.add(log)

def handle_event(
    db: Session,
    place_id: str,
    event: str,
    capacity_limit: int
):
    place = get_or_create_place(db, place_id, capacity_limit)

    # -------- ENTER --------
    if event == "enter":

        # 🚫 محاولة دخول بعد الامتلاء (الشخص رقم 11)
        if place.current_count >= place.capacity:
            place.state = "FULL"
            db.commit()
            return {
                "status": "OK",
                "state": "FULL",
                "current_count": place.current_count,
                "portal_url": f"http://gate.local/portal/{place_id}"
            }

        # ✅ دخول مسموح (حتى 10)
        place.current_count += 1

    # -------- EXIT --------
    elif event == "exit":
        place.current_count = max(0, place.current_count - 1)

    else:
        raise ValueError("Invalid event")

    # تحديث الحالة
    update_place_state(place)
    log_event(db, place_id, event, place.current_count)
    db.commit()

    return {
        "status": "OK",
        "state": place.state,
        "current_count": place.current_count,
        "portal_url": None
    }



