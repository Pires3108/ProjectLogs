from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import get_settings
from app.jobs.tasks import process_job
from app.main import app


def test_internal_worker_endpoint_requires_secret(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(process_job, "run", calls.append)
    monkeypatch.setattr(
        get_settings(), "internal_task_secret", SecretStr("synthetic-internal-secret")
    )
    client = TestClient(app)

    unauthorized = client.post("/internal/jobs/00000000-0000-0000-0000-000000000001/process")
    authorized = client.post(
        "/internal/jobs/00000000-0000-0000-0000-000000000001/process",
        headers={"X-Internal-Task-Token": "synthetic-internal-secret"},
    )

    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"]["code"] == "INTERNAL_TASK_UNAUTHORIZED"
    assert authorized.status_code == 204
    assert calls == ["00000000-0000-0000-0000-000000000001"]
