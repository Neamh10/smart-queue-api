from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EventIn(BaseModel):
    place_id: str          
    event: str             # enter | exit
    time: Optional[datetime] = None
    
class EventResponse(BaseModel):
    status: str
    current_count: int
    message: Optional[str] = None


class StatusResponse(BaseModel):
    place_id: str
    current_count: int

class EventLog(BaseModel):
    time: datetime
    current_count: int
    event: str


class StatusResponse(BaseModel):
    place_id: str
    current_count: int


class EventOut(BaseModel):
    time: datetime
    current_count: int
    event: str




