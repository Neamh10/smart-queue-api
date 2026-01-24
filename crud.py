from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
from models import Place, VisitEvent, Reservation

CAPACITY_LIMIT = 10
RESERVATION_TIMEOUT = 120  # seconds


# =========================
# Utils
# =========================
def generate_token():
    return uuid.uuid4().hex[:8].upper()


# =========================
# MAIN EVENT HANDLER
# =========================
def handle_event(db: Session, place_id: str, event: str, time, capacity_limit):

    place = get_or_create_place(db, place_id, capacity_limit)

    if event == "enter":
        if place.current_count >= place.capacity:
            update_place_state(place)
            db.commit()
            return {
                "status": "OK",
                "state": "FULL",
                "current_count": place.current_count,
                "portal_url": f"http://gate.local/portal/{place_id}"
            }

        place.current_count += 1

    elif event == "exit":
        place.current_count = max(0, place.current_count - 1)

    update_place_state(place)
    log_event(...)
    db.commit()

    return {
        "status": "OK",
        "state": place.state,
        "current_count": place.current_count
    }


# =========================
# CREATE RESERVATION
# =========================
def create_reservation(db: Session, from_place: str, to_place: str):
    token = generate_token()

    reservation = Reservation(
        token=token,
        from_place=from_place,
        to_place=to_place,
        expires_at=datetime.utcnow() + timedelta(seconds=RESERVATION_TIMEOUT)
    )

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return reservation


# =========================
# CONFIRM RESERVATION
# =========================
def confirm_reservation(db: Session, token: str, place_id: str):
    reservation = db.query(Reservation).filter_by(token=token).first()

    if not reservation:
        return None, "INVALID"

    if reservation.to_place != place_id:
        return None, "WRONG_PLACE"

    if reservation.expires_at < datetime.utcnow():
        db.delete(reservation)
        db.commit()
        return None, "EXPIRED"

    # ✅ تأكد من وجود المكان
    place = db.query(Place).filter_by(place_id=place_id).first()
    if not place:
        place = Place(
            place_id=place_id,
            capacity=CAPACITY_LIMIT,
            current_count=0
        )
        db.add(place)
        db.commit()
        db.refresh(place)

    # دخول حقيقي
    place.current_count += 1

    # حذف الحجز فورًا
    db.delete(reservation)

    db.commit()
    return None, "ENTERED"



# =========================
# ACTIVE RESERVATIONS
# =========================
def get_active_reservations(db: Session):
    return db.query(Reservation).order_by(
        Reservation.expires_at.asc()
    ).all()


# =========================
# CLEANUP
# =========================
def cleanup_reservations(db: Session):
    now = datetime.utcnow()

    expired = db.query(Reservation).filter(
        Reservation.expires_at < now
    ).all()

    for r in expired:
        db.delete(r)

    db.commit()



