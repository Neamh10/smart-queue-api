from sqlalchemy.orm import Session
from datetime import datetime
from models import Place, VisitEvent

def handle_event(
    db: Session,
    place_id: str,
    event: str,
    time: datetime | None,
    capacity_limit: int = 10
):
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

    if event == "enter":
        if place.current_count >= place.capacity:
            return {
                "status": "FULL",
                "current_count": place.current_count,
                "message": "Capacity reached"
            }
        place.current_count += 1

    elif event == "exit":
        place.current_count = max(0, place.current_count - 1)

    log = VisitEvent(
        place_id=place_id,
        event=event,
        current_count=place.current_count,
        time=time or datetime.utcnow()
    )

    db.add(log)
    db.commit()
    db.refresh(place)

    return {
        "status": "OK",
        "current_count": place.current_count,
        "message": "Event processed",
        "payload": {
            "place_id": place_id,
            "current_count": place.current_count,
            "event": event,
            "time": log.time.isoformat()
        }
    }
