from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import Place, VisitEvent

def handle_event(db: Session, place_id: str, event: str, event_id: int, time):

    # 1️⃣ تحقق هل event_id مسجّل سابقًا (Retry)
    existing = db.query(VisitEvent).filter(
        VisitEvent.event_id == event_id
    ).first()

    if existing:
        place = db.query(Place).filter(Place.place_id == place_id).first()
        return {
            "status": "OK",
            "current_count": place.current_count,
            "message": "Duplicate event ignored"
        }

    # 2️⃣ احصل على المكان
    place = db.query(Place).filter(Place.place_id == place_id).first()

    if not place:
        place = Place(place_id=place_id, capacity=10, current_count=0)
        db.add(place)
        db.commit()
        db.refresh(place)

    # 3️⃣ منطق الدخول / الخروج
    if event == "enter":
        if place.current_count >= place.capacity:
            return {
                "status": "FULL",
                "current_count": place.current_count,
                "message": "Capacity reached"
            }
        place.current_count += 1

    elif event == "exit":
        if place.current_count > 0:
            place.current_count -= 1

    # 4️⃣ تسجيل الحدث
    log = VisitEvent(
        place_id=place_id,
        event=event,
        event_id=event_id,
        time=time
    )

    db.add(log)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {
            "status": "OK",
            "current_count": place.current_count,
            "message": "Duplicate ignored (race)"
        }

    db.refresh(place)

    return {
        "status": "OK",
        "current_count": place.current_count,
        "message": "Event registered"
    }
