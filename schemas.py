from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ================== INPUT SCHEMA ==================
class EventIn(BaseModel):
    place_id: str
    event: str  # "enter" | "exit"
    time: Optional[datetime] = None


# ================== RESPONSE SCHEMA ==================
class EventResponse(BaseModel):
    status: str           # OK | FULL
    current_count: int
    message: str


# ================== EVENT OUT (HISTORY) ==================
class EventOut(BaseModel):
    place_id: str
    event: str
    time: datetime

    class Config:
        from_attributes = True
