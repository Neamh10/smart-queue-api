from sqlalchemy.orm import Session
#from models import Place, VisitEvent
from models import Place, Event
from schemas import EventIn

def get_place(db: Session, place_id: str) -> Place:
    place = db.query(Place).filter(Place.place_id == place_id).first()
    if not place:
        place = Place(place_id=place_id, current_count=0, capacity=10)
        db.add(place)
        db.commit()
        db.refresh(place)
    return place


def handle_event(db: Session, place_id: str, event: str, time, event_id: int):

    # منع التكرار (idempotency)
    exists = db.query(Event).filter(Event.event_id == event_id).first()
    if exists:
        return {
            "status": "OK",
            "current_count": exists.place.current_count,
            "message": "Duplicate event ignored"
        }

    place = db.query(Place).filter(Place.place_id == place_id).first()
    if not place:
        place = Place(place_id=place_id, capacity=10, current_count=0)
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
        if place.current_count > 0:
            place.current_count -= 1

    log = Event(
        event_id=event_id,
        place_id=place_id,
        event=event,
        time=time
    )

    db.add(log)
    db.commit()
    db.refresh(place)

    return {
        "status": "OK",
        "current_count": place.current_count,
        "message": "Event registered"
    }
