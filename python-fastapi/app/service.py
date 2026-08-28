from .errors import ServiceError
from .models import Event, EventInput
from .store import MemoryStore


class EventService:
    def __init__(self, store: MemoryStore):
        self.store = store

    def create(self, data: EventInput) -> Event:
        raise NotImplementedError

