import hmac
from typing import Annotated

from fastapi import APIRouter, Response, Security
from fastapi.security import APIKeyHeader

from app.config import get_settings
from app.errors import ApiError
from app.jobs.tasks import process_job

router = APIRouter(include_in_schema=False)
internal_header = APIKeyHeader(name="X-Internal-Task-Token", auto_error=False)


@router.post("/internal/jobs/{job_id}/process", status_code=204)
def process_internal_job(
    job_id: str,
    token: Annotated[str | None, Security(internal_header)],
) -> Response:
    expected = get_settings().internal_task_secret.get_secret_value()
    if not token or not hmac.compare_digest(token, expected):
        raise ApiError(
            status_code=401,
            code="INTERNAL_TASK_UNAUTHORIZED",
            message="A chamada interna não está autorizada.",
        )
    process_job.run(job_id)
    return Response(status_code=204)
