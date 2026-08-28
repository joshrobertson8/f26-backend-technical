from .errors import ServiceError
from .models import Event, EventInput
from .store import MemoryStore


class EventService:
    def __init__(self, store: MemoryStore):
        self.store = store

    def create(self, data: EventInput) -> Event:
        raise NotImplementedError

    def read(self, event_id: str) -> Event:
        raise NotImplementedError

    def update(self, event_id: str, data: EventInput) -> Event:
        raise NotImplementedError

    def delete(self, event_id: str) -> None:
        raise NotImplementedError
