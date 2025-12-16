from sqlalchemy.orm import Session
from models import Place, VisitEvent
from schemas import EventIn

def get_place(db: Session, place_id: str) -> Place:
    place = db.query(Place).filter(Place.place_id == place_id).first()
    if not place:
        place = Place(place_id=place_id, current_count=0, capacity=10)
        db.add(place)
        db.commit()
        db.refresh(place)
    return place

def handle_event(db: Session, event_data: EventIn):

    # Duplicate protection
    existing = db.query(VisitEvent)\
        .filter(VisitEvent.event_id == event_data.event_id)\
        .first()

    place = get_place(db, event_data.place_id)

    if existing:
        return {
            "status": "OK",
            "current_count": place.current_count,
            "message": "Duplicate event ignored"
        }

    # ENTER
    if event_data.event == "enter":
        if place.current_count >= place.capacity:
            return {
                "status": "FULL",
                "current_count": place.current_count,
                "message": "Capacity reached"
            }
        place.current_count += 1

    # EXIT
    elif event_data.event == "exit":
        if place.current_count > 0:
            place.current_count -= 1

    log = VisitEvent(
        place_id=event_data.place_id,
        event=event_data.event,
        event_id=event_data.event_id,
        time=event_data.time
    )

    db.add(log)
    db.commit()
    db.refresh(place)

    return {
        "status": "OK",
        "current_count": place.current_count,
        "message": "Event registered"
    }
