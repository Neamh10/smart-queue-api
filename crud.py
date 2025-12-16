from sqlalchemy.orm import Session
from models import Place, VisitEvent

def handle_event(db: Session, place_id: str, event: str, time):

    place = db.query(Place).filter(Place.place_id == place_id).first()

    if not place:
        place = Place(place_id=place_id, current_count=0, capacity=10)
        db.add(place)
        db.commit()
        db.refresh(place)

    # ========== ENTER ==========
    if event == "enter":
        if place.current_count >= place.capacity:
            return {
                "status": "FULL",
                "current_count": place.current_count,
                "message": "Capacity reached"
            }

        place.current_count += 1

    # ========== EXIT ==========
    elif event == "exit":
        if place.current_count > 0:
            place.current_count -= 1

    # Log event
    log = VisitEvent(
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
