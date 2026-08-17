from app.jobs.dispatch import CloudTasksDispatcher


class FakeCloudTasksClient:
    def __init__(self) -> None:
        self.request = None

    def queue_path(self, project: str, location: str, queue: str) -> str:
        return f"projects/{project}/locations/{location}/queues/{queue}"

    def task_path(self, project: str, location: str, queue: str, task: str) -> str:
        return f"projects/{project}/locations/{location}/queues/{queue}/tasks/{task}"

    def create_task(self, request) -> None:
        self.request = request


def test_dispatches_authenticated_cloud_task_without_source_content() -> None:
    client = FakeCloudTasksClient()
    dispatcher = CloudTasksDispatcher(
        project="synthetic-project",
        location="us-central1",
        queue="ataviva-jobs",
        worker_url="https://worker.invalid/",
        service_account_email="worker@synthetic-project.iam.gserviceaccount.com",
        internal_token="synthetic-internal-token",
        client=client,  # type: ignore[arg-type]
    )

    dispatcher("00000000-0000-0000-0000-000000000001")

    task = client.request["task"]
    request = task["http_request"]
    assert request["url"].endswith("/internal/jobs/00000000-0000-0000-0000-000000000001/process")
    assert request["oidc_token"]["audience"] == "https://worker.invalid"
    assert request["headers"]["X-Internal-Task-Token"] == "synthetic-internal-token"
    assert "fonte" not in str(task).lower()
