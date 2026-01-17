from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import uuid

from models import Place, VisitEvent, Reservation


CAPACITY_LIMIT = 10
RESERVATION_TIMEOUT = 120  # seconds


# =========================
# Utils
# =========================
def generate_token() -> str:
    return uuid.uuid4().hex[:8].upper()


# =========================
# RESERVATION (LOCKED)
# =========================
def create_reservation_locked(
    db: Session,
    from_place: str,
    to_place: str
) -> Reservation:
    token = generate_token()

    # 🔐 Lock target place
    target = (
        db.query(Place)
        .filter_by(place_id=to_place)
        .with_for_update()
        .first()
    )

    if not target:
        target = Place(
            place_id=to_place,
            capacity=CAPACITY_LIMIT,
            current_count=0
        )
        db.add(target)
        db.flush()

    if target.current_count >= target.capacity:
        raise ValueError("Target place full")

    # حجز فعلي (زيادة العداد فورًا)
    target.current_count += 1

    reservation = Reservation(
        token=token,
        from_place=from_place,
        to_place=to_place,
        expires_at=datetime.utcnow() + timedelta(seconds=RESERVATION_TIMEOUT),
        confirmed=False
    )

    db.add(reservation)
    db.flush()

    return reservation


# =========================
# MAIN EVENT HANDLER
# =========================
def handle_event(
    db: Session,
    place_id: str,
    event: str,
    time: datetime | None,
    capacity_limit: int
):
    try:
        # 🔐 Lock current place
        place = (
            db.query(Place)
            .filter_by(place_id=place_id)
            .with_for_update()
            .first()
        )

        if not place:
            place = Place(
                place_id=place_id,
                capacity=capacity_limit,
                current_count=0
            )
            db.add(place)
            db.flush()

        # =========================
        # ENTER
        # =========================
        if event == "enter":
            if place.current_count >= place.capacity:
                redirect_place = "hall_2"

                reservation = create_reservation_locked(
                    db,
                    from_place=place_id,
                    to_place=redirect_place
                )

                db.commit()  # 🔓 release locks + persist

                return {
                    "status": "FULL",
                    "place_id": place_id,
                    "current_count": place.current_count,
                    "redirect_to": reservation.to_place,
                    "token": reservation.token,
                    "message": "Redirect to another hall"
                }

            place.current_count += 1

        # =========================
        # EXIT
        # =========================
        elif event == "exit":
            place.current_count = max(0, place.current_count - 1)

        else:
            raise ValueError("Invalid event type")

        # =========================
        # LOG EVENT
        # =========================
        log = VisitEvent(
            place_id=place_id,
            event=event,
            current_count=place.current_count,
            time=time or datetime.utcnow()
        )

        db.add(log)
        db.commit()

        return {
            "status": "OK",
            "place_id": place_id,
            "current_count": place.current_count,
            "message": "Event processed"
        }

    except Exception:
        db.rollback()
        raise


# =========================
# CONFIRM RESERVATION
# =========================
def confirm_reservation(
    db: Session,
    token: str,
    place_id: str
):
    try:
        reservation = (
            db.query(Reservation)
            .filter_by(token=token)
            .with_for_update()
            .first()
        )

        if not reservation:
            return None, "INVALID"

        if reservation.confirmed:
            return None, "ALREADY_CONFIRMED"

        if reservation.to_place != place_id:
            return None, "WRONG_PLACE"

        if reservation.expires_at < datetime.utcnow():
            place = (
                db.query(Place)
                .filter_by(place_id=reservation.to_place)
                .with_for_update()
                .first()
            )

            if place:
                place.current_count = max(0, place.current_count - 1)

            db.delete(reservation)
            db.commit()
            return None, "EXPIRED"

        reservation.confirmed = True
        db.commit()
        return reservation, "CONFIRMED"

    except Exception:
        db.rollback()
        raise


# =========================
# READ OPERATIONS
# =========================
def get_active_reservations(db: Session):
    return (
        db.query(Reservation)
        .order_by(Reservation.expires_at.asc())
        .all()
    )


def cleanup_expired_reservations(db: Session):
    expired = (
        db.query(Reservation)
        .filter(Reservation.expires_at < datetime.utcnow())
        .all()
    )

    for r in expired:
        place = (
            db.query(Place)
            .filter_by(place_id=r.to_place)
            .with_for_update()
            .first()
        )

        if place:
            place.current_count = max(0, place.current_count - 1)

        db.delete(r)

    db.commit()
