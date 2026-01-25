from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import Place, VisitEvent, Reservation

# =========================
# Config
# =========================
RESERVATION_TTL = 120  # 2 minutes


# =========================
# Reservation Logic
# =========================
def create_reservation(db: Session, from_place: str, to_place: str):
    now = datetime.utcnow()

    reservation = Reservation(
        from_place=from_place,
        to_place=to_place,
        status="ACTIVE",
        created_at=now,
        expires_at=now + timedelta(seconds=RESERVATION_TTL)
    )

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return reservation


def cleanup_expired_reservations(db: Session):
    now = datetime.utcnow()

    expired = db.query(Reservation).filter(
        Reservation.status == "ACTIVE",
        Reservation.expires_at < now
    ).all()

    for r in expired:
        r.status = "EXPIRED"

    db.commit()


# =========================
# Place Logic
# =========================
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
    place.state = "FULL" if place.current_count > place.capacity else "NORMAL"

def log_event(db: Session, place_id: str, event: str, count: int):
    log = VisitEvent(
        place_id=place_id,
        event=event,
        current_count=count
    )
    db.add(log)


# =========================
# Main Event Handler
# =========================
def handle_event(
    db: Session,
    place_id: str,
    event: str,
    capacity_limit: int
):
    # تنظيف الحجوزات المنتهية
    cleanup_expired_reservations(db)

    place = get_or_create_place(db, place_id, capacity_limit)

    # -------- ENTER --------
    if event == "enter":

        # 🚫 الشخص رقم (capacity + 1)
        if place.current_count >= place.capacity:
            update_place_state(place)
            db.commit()
            return {
                "status": "OK",
                "state": "FULL",
                "current_count": place.current_count,
                "portal_url": f"http://gate.local/portal/{place_id}"
            }

        # ✅ دخول مسموح
        place.current_count += 1

    # -------- EXIT --------
    elif event == "exit":
        place.current_count = max(0, place.current_count - 1)

    else:
        raise ValueError("Invalid event")

    # تحديث الحالة + تسجيل الحدث
    update_place_state(place)
    log_event(db, place_id, event, place.current_count)
    db.commit()

    return {
        "status": "OK",
        "state": place.state,
        "current_count": place.current_count,
        "portal_url": f"http://gate.local/portal/{place_id}" if place.state == "FULL" else None
    }

