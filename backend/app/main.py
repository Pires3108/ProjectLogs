from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.errors import ApiError, api_exception_handler, validation_exception_handler
from app.ingestion.upload_routes import router as uploads_router
from app.jobs.internal_routes import router as internal_jobs_router
from app.jobs.routes import router as jobs_router
from app.observability import configure_logging, observe_request
from app.observability import router as observability_router
from app.routes import router

settings = get_settings()
configure_logging()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para gerar documentação estruturada a partir de fontes de reuniões.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ApiError, api_exception_handler)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


app.include_router(router)
app.include_router(jobs_router)
app.include_router(uploads_router)
app.include_router(internal_jobs_router)
app.include_router(observability_router)
app.middleware("http")(observe_request)
