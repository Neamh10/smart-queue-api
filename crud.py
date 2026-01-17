from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

from models import Place, Reservation


RESERVATION_TIMEOUT = 120  # seconds


# ======================
# Helpers
# ======================
def get_or_create_place(db: Session, place_id: str, capacity_limit: int):
    place = db.query(Place).filter_by(id=place_id).first()
    if not place:
        place = Place(
            id=place_id,
            current_count=0,
            capacity=capacity_limit
        )
        db.add(place)
        db.commit()
        db.refresh(place)
    return place


def cleanup_expired_reservations(db: Session):
    now = datetime.utcnow()
    expired = (
        db.query(Reservation)
        .filter(
            Reservation.expires_at < now,
            Reservation.confirmed == False
        )
        .all()
    )

    for r in expired:
        place = db.query(Place).filter_by(id=r.to_place).first()
        if place and place.current_count > 0:
            place.current_count -= 1
        db.delete(r)

    db.commit()


def find_available_place(db: Session, exclude_place: str):
    return (
        db.query(Place)
        .filter(
            Place.id != exclude_place,
            Place.current_count < Place.capacity
        )
        .first()
    )


# ======================
# Core Logic
# ======================
def handle_event(
    db: Session,
    place_id: str,
    event: str,
    time,
    capacity_limit: int
):
    cleanup_expired_reservations(db)

    place = get_or_create_place(db, place_id, capacity_limit)

    if event == "exit":
        if place.current_count > 0:
            place.current_count -= 1
            db.commit()

        return {
            "status": "OK",
            "place_id": place_id,
            "current_count": place.current_count,
            "redirect_to": None,
            "token": None
        }

    # ========= ENTER =========
    if place.current_count < place.capacity:
        place.current_count += 1
        db.commit()

        return {
            "status": "OK",
            "place_id": place_id,
            "current_count": place.current_count,
            "redirect_to": None,
            "token": None
        }

    # ========= FULL =========
    alt_place = find_available_place(db, place_id)

    if not alt_place:
        return {
            "status": "FULL",
            "place_id": place_id,
            "current_count": place.current_count,
            "redirect_to": None,
            "token": None,
            "message": "All places are full"
        }

    # 🔐 Create Reservation
    token = secrets.token_hex(4)

    reservation = Reservation(
        token=token,
        from_place=place_id,
        to_place=alt_place.id,
        expires_at=datetime.utcnow() + timedelta(seconds=RESERVATION_TIMEOUT),
        confirmed=False
    )

    # 🔒 Reserve spot immediately
    alt_place.current_count += 1

    db.add(reservation)
    db.commit()

    return {
        "status": "FULL",
        "place_id": place_id,
        "current_count": place.current_count,
        "redirect_to": alt_place.id,
        "token": token
    }


# ======================
# Confirm Reservation
# ======================
def confirm_reservation(db: Session, token: str, place_id: str):
    cleanup_expired_reservations(db)

    reservation = (
        db.query(Reservation)
        .filter_by(token=token, to_place=place_id)
        .first()
    )

    if not reservation:
        return None, "INVALID_TOKEN"

    if reservation.confirmed:
        return reservation, "ALREADY_CONFIRMED"

    if reservation.expires_at < datetime.utcnow():
        return None, "EXPIRED"

    reservation.confirmed = True
    db.commit()

    return reservation, "CONFIRMED"


def get_active_reservations(db: Session):
    cleanup_expired_reservations(db)
    return db.query(Reservation).all()
