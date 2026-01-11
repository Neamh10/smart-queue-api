from sqlalchemy import Column, String, Integer, DateTime, Boolean
from datetime import datetime, timedelta
from database import Base


class Place(Base):
    __tablename__ = "places"

    place_id = Column(String, primary_key=True, index=True)
    current_count = Column(Integer, default=0)
    capacity = Column(Integer, default=10)


class Reservation(Base):
    __tablename__ = "reservations"

    token = Column(String, primary_key=True, index=True)
    from_place = Column(String, index=True)
    to_place = Column(String, index=True)
    expires_at = Column(DateTime)
    confirmed = Column(Boolean, default=False)

    @staticmethod
    def expiry(minutes=3):
        return datetime.utcnow() + timedelta(minutes=minutes)
