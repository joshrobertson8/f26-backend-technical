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

