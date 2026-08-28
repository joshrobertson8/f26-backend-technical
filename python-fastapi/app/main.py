from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .controller import make_router
from .errors import ServiceError
from .service import EventService
from .store import MemoryStore


def create_app() -> FastAPI:
    app = FastAPI(title="Event invitations API")
    store = MemoryStore()
    service = EventService(store)

