from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str


class EventInput(BaseModel):
    model_config = {"extra": "forbid", "strict": True}

    title: str
    description: str = ""

    inviteeIds: list[str] = []


class Event(EventInput):
    id: str
