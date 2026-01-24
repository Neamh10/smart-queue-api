from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from database import Base

class Place(Base):
    __tablename__ = "places"

    id = Column(String, primary_key=True)   # hall_1, hall_2
    capacity = Column(Integer, default=10)
    current_count = Column(Integer, default=0)
    state = Column(String, default="NORMAL")  # NORMAL | FULL

class VisitEvent(Base):
    __tablename__ = "visit_events"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String, index=True)
    event = Column(String)  # enter | exit
    current_count = Column(Integer)
    time = Column(DateTime, default=datetime.utcnow)
 








