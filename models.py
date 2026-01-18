from sqlalchemy import Column, String, Integer, DateTime, Boolean
from datetime import datetime
from database import Base

class Place(Base):
    __tablename__ = "places"

    place_id = Column(String, primary_key=True, index=True)
    current_count = Column(Integer, default=0)
    capacity = Column(Integer, default=10)


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




