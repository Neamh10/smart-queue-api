from sqlalchemy import Column, String, Integer, DateTime, Boolean
from datetime import datetime
from database import Base
from enum import Enum


cclass Place(Base):
    __tablename__ = "places"

    id = Column(String, primary_key=True)
    name = Column(String)
    capacity = Column(Integer)
    current_count = Column(Integer, default=0)
    state = Column(String, default="NORMAL")  


class VisitEvent(Base):
    __tablename__ = "visit_events"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String, index=True)
    event = Column(String)  # enter | exit
    current_count = Column(Integer)
    time = Column(DateTime, default=datetime.utcnow)

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)

    from_place = Column(String, index=True)
    to_place = Column(String, index=True)

    confirmed = Column(Boolean, default=False)
    archived = Column(Boolean, default=False)
    expires_at = Column(DateTime)  

class PlaceState(str, Enum):
    NORMAL = "NORMAL"
    FULL = "FULL"






