from fastapi import APIRouter, Response

from .models import Event, EventInput
from .service import EventService
from .store import MemoryStore
from .validation import validate_event_input


def make_router(service: EventService, store: MemoryStore) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/health")
    def health():
        return {"status": "ok"}

    @router.get("/users")
    def users():
        return list(store.users.values())

    @router.post("/events", status_code=201, response_model=Event)
    def create(data: EventInput):
        validate_event_input(data)

        return service.create(data)

    @router.get("/events/{event_id}", response_model=Event)
    def read(event_id: str):
        return service.read(event_id)

    @router.put("/events/{event_id}", response_model=Event)
    def update(event_id: str, data: EventInput):
        validate_event_input(data)

