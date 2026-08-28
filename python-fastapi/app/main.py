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

    app.include_router(make_router(service, store))

    @app.exception_handler(ServiceError)
    async def service_error(_request: Request, error: ServiceError):
        return JSONResponse({"error": str(error)}, status_code=error.status)

    @app.exception_handler(NotImplementedError)
    async def unfinished(_request: Request, _error: NotImplementedError):
        return JSONResponse({"error": "Implement the event service"}, status_code=501)

