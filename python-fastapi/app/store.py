from .models import Event, User


class MemoryStore:
    def __init__(self):
        self.events: dict[str, Event] = {}
        self.next_id = 1

