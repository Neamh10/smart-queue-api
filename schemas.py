from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EventIn(BaseModel):
    place_id: str
    event: str
    time: Optional[datetime] = None


class EventResponse(BaseModel):
    status: str
    place_id: str
    current_count: int
    redirect_to: Optional[str]
    token: Optional[str]
    message: Optional[str] = None


class ConfirmReservationIn(BaseModel):
    token: str
    place_id: str


class ConfirmReservationResponse(BaseModel):
    status: str
    place_id: str


class ReservationOut(BaseModel):
    token: str
    from_place: str
    to_place: str
    expires_at: datetime
    confirmed: bool

    class Config:
        from_attributes = True
