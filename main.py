import os
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import crud
import schemas
from manager import ConnectionManager


# ======================
# App Init
# ======================
app = FastAPI(
    title="Smart Queue Backend",
    version="1.0.0",
    description="Smart Queue & Reservation System API"
)

Base.metadata.create_all(bind=engine)


# ======================
# Security (API KEY)
# ======================
API_KEY = os.getenv("SMARTQUEUE_API_KEY", "DEV-KEY-CHANGE-ME")

api_key_header = APIKeyHeader(
    name="X-API-KEY",
    auto_error=False
)


def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


# ======================
# Swagger API Key Auth
# ======================
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-KEY",
        }
    }

    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", []).append(
                {"ApiKeyAuth": []}
            )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ======================
# Config
# ======================
CAPACITY_LIMIT = 10
manager = ConnectionManager()


# ======================
# Middleware (CORS)
# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:5500"
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True
)


# ======================
# Root
# ======================
@app.get("/")
def root():
    return {
        "status": "OK",
        "service": "Smart Queue Backend"
    }


# ======================
# EVENT (ESP32 → Server)
# ======================
@app.post(
    "/event",
    response_model=schemas.EventResponse,
    dependencies=[Depends(verify_api_key)]
)
async def receive_event(
    event: schemas.EventIn,
    db: Session = Depends(get_db)
):
    result = crud.handle_event(
        db=db,
        place_id=event.place_id,
        event=event.event,
        time=event.time,
        capacity_limit=CAPACITY_LIMIT
    )

    await manager.broadcast(
        place_id=event.place_id,
        data={
            "place_id": event.place_id,
            "current_count": result["current_count"],
            "status": result["status"]
        }
    )

    return result


# ======================
# CONFIRM RESERVATION
# ======================
@app.post(
    "/confirm",
    response_model=schemas.ConfirmReservationResponse,
    dependencies=[Depends(verify_api_key)]
)
def confirm_reservation(
    data: schemas.ConfirmReservationIn,
    db: Session = Depends(get_db)
):
    reservation, status = crud.confirm_reservation(
        db=db,
        token=data.token,
        place_id=data.place_id
    )

    if status != "CONFIRMED":
        raise HTTPException(
            status_code=400,
            detail=status
        )

    return {
        "status": "CONFIRMED",
        "place_id": data.place_id
    }


# ======================
# RESERVATIONS (Dashboard)
# ======================
@app.get(
    "/reservations",
    response_model=list[schemas.ReservationOut],
    dependencies=[Depends(verify_api_key)]
)
def list_reservations(
    db: Session = Depends(get_db)
):
    crud.cleanup_expired_reservations(db)
    return crud.get_active_reservations(db)


# ======================
# WebSocket (Dashboard)
# ======================
@app.websocket("/ws/{place_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    place_id: str
):
    await manager.connect(websocket, place_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, place_id)
