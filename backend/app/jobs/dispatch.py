from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from google.cloud import tasks_v2
from google.protobuf import duration_pb2

from app.config import get_settings
from app.errors import ApiError
from app.jobs.tasks import enqueue_job, process_job

JobDispatcher = Callable[[str], None]
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ataviva-job")


def dispatch_in_process(job_id: str) -> None:
    """Best-effort dispatcher for a single free web instance without a paid worker."""
    _executor.submit(process_job.run, job_id)


class CloudTasksDispatcher:
    def __init__(
        self,
        *,
        project: str,
        location: str,
        queue: str,
        worker_url: str,
        service_account_email: str,
        internal_token: str,
        client: tasks_v2.CloudTasksClient | None = None,
    ) -> None:
        self.project = project
        self.location = location
        self.queue = queue
        self.worker_url = worker_url.rstrip("/")
        self.service_account_email = service_account_email
        self.internal_token = internal_token
        self.client = client or tasks_v2.CloudTasksClient()

    def __call__(self, job_id: str) -> None:
        parent = self.client.queue_path(self.project, self.location, self.queue)
        task = {
            "name": self.client.task_path(self.project, self.location, self.queue, f"job-{job_id}"),
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{self.worker_url}/internal/jobs/{job_id}/process",
                "oidc_token": {
                    "service_account_email": self.service_account_email,
                    "audience": self.worker_url,
                },
                "headers": {"X-Internal-Task-Token": self.internal_token},
            },
            "dispatch_deadline": duration_pb2.Duration(seconds=1800),
        }
        self.client.create_task(request={"parent": parent, "task": task})


def get_job_dispatcher() -> JobDispatcher:
    settings = get_settings()
    if settings.job_dispatcher == "in_process":
        return dispatch_in_process
    if settings.job_dispatcher == "cloud_tasks":
        required = {
            "google_cloud_project": settings.google_cloud_project,
            "cloud_tasks_worker_url": settings.cloud_tasks_worker_url,
            "cloud_tasks_service_account_email": settings.cloud_tasks_service_account_email,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ApiError(
                status_code=503,
                code="QUEUE_NOT_CONFIGURED",
                message="A fila serverless não está configurada.",
                details={"missing": missing},
            )
        return CloudTasksDispatcher(
            project=settings.google_cloud_project or "",
            location=settings.google_cloud_location,
            queue=settings.google_cloud_tasks_queue,
            worker_url=settings.cloud_tasks_worker_url or "",
            service_account_email=settings.cloud_tasks_service_account_email or "",
            internal_token=settings.internal_task_secret.get_secret_value(),
        )
    if settings.job_dispatcher != "celery":
        raise ApiError(
            status_code=503,
            code="QUEUE_NOT_CONFIGURED",
            message="O dispatcher de jobs configurado não é suportado.",
        )
    return enqueue_job
