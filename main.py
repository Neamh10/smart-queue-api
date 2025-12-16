from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database import SessionLocal, engine
import models
from schemas import EventIn, EventResponse
from crud import handle_event

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Queue Backend")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/event", response_model=EventResponse)
def receive_event(event: EventIn, db: Session = Depends(get_db)):
    result = handle_event(
        db=db,
        place_id=event.place_id,
        event=event.event,
        time=event.time
    )
    return result
