from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base
from datetime import datetime


class Place(Base):
    __tablename__ = "places"

    id = Column(String, primary_key=True, index=True)
    current_count = Column(Integer, default=0)
    capacity = Column(Integer, default=10)


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    from_place = Column(String, index=True)
    to_place = Column(String, index=True)
    expires_at = Column(DateTime)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
