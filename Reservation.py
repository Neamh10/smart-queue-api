from sqlalchemy import Column, String, DateTime, Boolean
from datetime import datetime, timedelta
from database import Base

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
