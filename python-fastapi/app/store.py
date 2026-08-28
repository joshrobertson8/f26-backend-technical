from .models import Event, User


class MemoryStore:
    def __init__(self):
        self.events: dict[str, Event] = {}
        self.next_id = 1

        self.users = {
            "u1": User(id="u1", name="Ada"),
            "u2": User(id="u2", name="Grace"),
            "u3": User(id="u3", name="Linus"),
        }

    def generate_id(self) -> str:
        event_id = f"event-{self.next_id}"
        self.next_id += 1

        return event_id
