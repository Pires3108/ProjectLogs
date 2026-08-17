import logging
import time

from fastapi import APIRouter, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pythonjsonlogger.json import JsonFormatter

HTTP_REQUESTS = Counter(
    "ataviva_http_requests_total", "HTTP requests", ["method", "path", "status"]
)
HTTP_DURATION = Histogram(
    "ataviva_http_request_duration_seconds", "HTTP request duration", ["method", "path"]
)
JOBS_PROCESSED = Counter("ataviva_jobs_processed_total", "Processed jobs", ["status"])
LLM_REQUESTS = Counter("ataviva_llm_requests_total", "LLM requests", ["provider", "result"])

router = APIRouter(tags=["observabilidade"])


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


async def observe_request(request: Request, call_next) -> Response:
    started = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    elapsed = time.perf_counter() - started
    HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    HTTP_DURATION.labels(request.method, path).observe(elapsed)
    logging.getLogger("ataviva.http").info(
        "request_completed",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": path,
            "status": response.status_code,
            "duration_ms": round(elapsed * 1000, 2),
        },
    )
    return response


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
