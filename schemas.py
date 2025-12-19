from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EventIn(BaseModel):
    place_id: str
    event: str          # enter | exit
    time: Optional[datetime] = None

class EventResponse(BaseModel):
    status: str
    current_count: int
    message: str
