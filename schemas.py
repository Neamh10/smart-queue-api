from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class EventIn(BaseModel):
    place_id: str
    event: Literal["enter", "exit"]
    time: datetime


class EventResponse(BaseModel):
    status: Literal["OK", "FULL"]
    current_count: int
    message: str
