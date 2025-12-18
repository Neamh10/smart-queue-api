from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EventIn(BaseModel):
    place_id: str
    event: str          
    time: Optional[datetime] = None


class EventResponse(BaseModel):
    status: str
    current_count: int
    message: str

