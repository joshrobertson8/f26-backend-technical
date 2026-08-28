from .errors import ServiceError
from .models import EventInput


def validate_event_input(data: EventInput):
    if data.title.strip() == "":
        raise ServiceError(400, "Invalid event body")
