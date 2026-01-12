from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ======================
# INPUT
# ======================
class EventIn(BaseModel):
    place_id: str              # hall_1
    event: str                 # enter | exit
    time: Optional[datetime] = None


class ConfirmReservationIn(BaseModel):
    token: str
    place_id: str


# ======================
# OUTPUT
# ======================
class EventResponse(BaseModel):
    status: str                # OK | FULL
    place_id: str
    current_count: int

    # FULL only
    redirect_to: Optional[str] = None
    token: Optional[str] = None

    # optional (for logs / dashboard)
    message: Optional[str] = None


class ConfirmReservationResponse(BaseModel):
    status: str                # CONFIRMED
    place_id: str


# ======================
# DASHBOARD
# ======================
class EventLog(BaseModel):
    time: datetime
    event: str
    current_count: int


class PlaceStatus(BaseModel):
    place_id: str
    current_count: int
    capacity: int
