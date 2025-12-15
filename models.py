from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class VisitEvent(Base):
    __tablename__ = "visit_events"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String, index=True)
    event = Column(String)          # enter | exit
    time = Column(DateTime)         # ISO time from ESP32
    created_at = Column(DateTime(timezone=True), server_default=func.now())
