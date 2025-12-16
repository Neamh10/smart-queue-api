from pydantic import BaseModel
from datetime import datetime

class EventIn(BaseModel):
    place_id: str
    event: str          # enter | exit
    event_id: int
    time: datetime

class EventResponse(BaseModel):
    status: str
    current_count: int
    message: str

