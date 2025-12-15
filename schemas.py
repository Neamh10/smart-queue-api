from pydantic import BaseModel
from datetime import datetime

class EventIn(BaseModel):
    place_id: str
    event: str          # enter | exit
    time: datetime      # ISO time

class EventResponse(BaseModel):
    status: str         # OK | FULL
    current_count: int
    message: str
