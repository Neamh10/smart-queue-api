from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ======================
# INPUT (ESP32 / Manual)
# ======================
class EventIn(BaseModel):
    place_id: str              # hall_1
    event: str                 # enter | exit
    time: Optional[datetime] = None


# ======================
# OUTPUT (ESP32 Response)
# ======================
class EventResponse(BaseModel):
    status: str                # OK
    state: str                 # NORMAL | FULL
    current_count: int
    portal_url: Optional[str] = None


# ======================
# DASHBOARD (WebSocket / Logs)
# ======================
class EventLog(BaseModel):
    time: datetime
    event: str
    current_count: int


class PlaceStatus(BaseModel):
    place_id: str
    current_count: int
    capacity: int
    state: str
