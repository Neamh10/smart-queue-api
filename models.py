from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class Place(Base):
    __tablename__ = "places"

    place_id = Column(String, primary_key=True, index=True)
    capacity = Column(Integer, nullable=False)
    current_count = Column(Integer, default=0)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String, index=True)
    event = Column(String)  # enter | exit
    time = Column(DateTime, default=datetime.utcnow)
