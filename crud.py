from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from models import Place, VisitEvent


def handle_event(
    db: Session,
    place_id: str,
    event: str,
    event_id: int | None,
    time: datetime | None,
    capacity_limit: int = 10
):
    # 1️⃣ Retry protection (ESP32)
    if event_id is not None:
        existing = db.query(VisitEvent).filter(
            VisitEvent.event_id == event_id
        ).first()
        if existing:
            place = db.query(Place).filter(
                Place.place_id == place_id
            ).first()
            return "OK", place.current_count if place else 0

    # 2️⃣ Get or create place
    place = db.query(Place).filter(
        Place.place_id == place_id
    ).first()

    if not place:
        place = Place(
            place_id=place_id,
            capacity=capacity_limit,
            current_count=0
        )
        db.add(place)
        db.commit()
        db.refresh(place)

    # 3️⃣ Business logic
    if event == "enter":
        if place.current_count >= place.capacity:
            return "FULL", place.current_count
        place.current_count += 1

    elif event == "exit":
        place.current_count = max(0, place.current_count - 1)

    else:
        raise ValueError("Invalid event type")

    # 4️⃣ Log event
    log = VisitEvent(
        place_id=place_id,
        event=event,
        event_id=event_id,
        time=time or datetime.utcnow()
    )

    db.add(log)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

    db.refresh(place)
    return "OK", place.current_count


def get_current_count(db: Session, place_id: str) -> int:
    place = db.query(Place).filter(
        Place.place_id == place_id
    ).first()
    return place.current_count if place else 0


def get_events(db: Session, place_id: str, limit: int = 10):
    return (
        db.query(VisitEvent)
        .filter(VisitEvent.place_id == place_id)
        .order_by(VisitEvent.time.desc())
        .limit(limit)
        .all()
    )
