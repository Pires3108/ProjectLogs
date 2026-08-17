from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.keys import issue_api_key
from app.auth.rate_limit import get_rate_limiter
from app.config import get_settings
from app.db.base import Base
from app.db.models import ApiKeyRecord
from app.db.session import get_db_session
from app.jobs.dispatch import get_job_dispatcher
from app.main import app


class FakeDirectStorage:
    def __init__(self) -> None:
        self.expected_size = 206_175_845

    def create_upload(self, source_id: str, extension: str, content_type: str, expires: int) -> str:
        assert extension == ".mp4"
        assert content_type == "video/mp4"
        return f"https://storage.invalid/sources/{source_id}.mp4"

    def size(self, source_id: str, extension: str) -> int:
        return self.expected_size


@pytest.fixture
def api(tmp_path: Path, monkeypatch) -> Iterator[tuple[TestClient, str, sessionmaker[Session]]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def session_override() -> Iterator[Session]:
        with factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = session_override
    app.dependency_overrides[get_job_dispatcher] = lambda: lambda _: None
    app.dependency_overrides[get_rate_limiter] = lambda: type(
        "NoopRateLimiter", (), {"check": lambda self, _: None}
    )()
    settings = get_settings()
    monkeypatch.setattr(settings, "upload_root", str(tmp_path / "uploads"))
    raw_key, record = issue_api_key("Test client", settings.api_key_pepper.get_secret_value())
    with factory() as session:
        session.add(record)
        session.commit()
    try:
        yield TestClient(app), raw_key, factory
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_create_and_get_queued_job(api) -> None:
    client, raw_key, _ = api
    response = client.post(
        "/v1/jobs",
        headers={"X-API-Key": raw_key},
        data={
            "perfil": "estudo",
            "toggles": '{"exercicios": true, "linha_do_tempo": true}',
        },
        files=[
            (
                "fontes",
                ("reuniao.md", b"# Reuniao\n\nConteudo sintetico para analise.", "text/markdown"),
            )
        ],
    )

    assert response.status_code == 202
    job = response.json()
    assert job["status"] == "queued"
    assert job["perfil"] == "estudo"
    assert job["toggles"]["exercicios"] is True
    assert job["toggles"]["linha_do_tempo"] is False
    assert job["avisos"][0]["toggle"] == "linha_do_tempo"
    assert job["fontes"][0]["formato"] == "md"
    assert job["fila_posicao"] == 1

    status = client.get(f"/v1/jobs/{job['id']}", headers={"X-API-Key": raw_key})
    assert status.status_code == 200
    assert status.json()["id"] == job["id"]
    assert status.json()["fila_estimativa_minutos"] == 5


def test_direct_upload_creates_job_and_ticket_is_single_use(api, monkeypatch) -> None:
    client, raw_key, _ = api
    storage = FakeDirectStorage()
    settings = get_settings()
    monkeypatch.setattr(settings, "storage_backend", "s3")
    monkeypatch.setattr("app.ingestion.upload_routes.create_source_storage", lambda _: storage)
    monkeypatch.setattr("app.jobs.routes.create_source_storage", lambda _: storage)

    upload = client.post(
        "/v1/uploads",
        headers={"X-API-Key": raw_key},
        json={
            "nome": "meeting.mp4",
            "tamanho_bytes": storage.expected_size,
            "content_type": "video/mp4",
        },
    )
    assert upload.status_code == 200
    payload = upload.json()
    assert payload["metodo"] == "PUT"
    assert payload["upload_url"].startswith("https://storage.invalid/")

    request = {
        "perfil": "organizacao",
        "toggles": {"linha_do_tempo": True},
        "tickets": [payload["ticket"]],
    }
    created = client.post(
        "/v1/jobs/from-uploads",
        headers={"X-API-Key": raw_key},
        json=request,
    )
    assert created.status_code == 202
    assert created.json()["fontes"][0]["tamanho_bytes"] == storage.expected_size

    replay = client.post(
        "/v1/jobs/from-uploads",
        headers={"X-API-Key": raw_key},
        json=request,
    )
    assert replay.status_code == 409
    assert replay.json()["error"]["code"] == "UPLOAD_ALREADY_USED"


def test_jobs_require_api_key(api) -> None:
    client, _, _ = api

    response = client.get("/v1/jobs/unknown")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "API_KEY_MISSING"


def test_rejects_revoked_and_expired_keys(api) -> None:
    client, _, factory = api
    settings = get_settings()
    revoked_key, revoked = issue_api_key("Revoked", settings.api_key_pepper.get_secret_value())
    revoked.revoked_at = datetime.now(UTC)
    expired_key, expired = issue_api_key(
        "Expired",
        settings.api_key_pepper.get_secret_value(),
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    with factory() as session:
        session.add_all([revoked, expired])
        session.commit()

    revoked_response = client.get("/v1/jobs/unknown", headers={"X-API-Key": revoked_key})
    expired_response = client.get("/v1/jobs/unknown", headers={"X-API-Key": expired_key})

    assert revoked_response.status_code == 401
    assert revoked_response.json()["error"]["code"] == "API_KEY_INVALID"
    assert expired_response.status_code == 401
    assert expired_response.json()["error"]["code"] == "API_KEY_EXPIRED"


def test_api_key_cannot_access_another_keys_job(api) -> None:
    client, raw_key, factory = api
    created = client.post(
        "/v1/jobs",
        headers={"X-API-Key": raw_key},
        data={"perfil": "backlog", "toggles": "{}"},
        files=[
            ("fontes", ("fonte.txt", b"Conteudo sintetico suficientemente longo.", "text/plain"))
        ],
    )
    job_id = created.json()["id"]
    settings = get_settings()
    other_key, other_record = issue_api_key(
        "Other client", settings.api_key_pepper.get_secret_value()
    )
    with factory() as session:
        session.add(other_record)
        session.commit()

    response = client.get(f"/v1/jobs/{job_id}", headers={"X-API-Key": other_key})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "JOB_NOT_FOUND"


def test_raw_api_key_is_never_stored(api) -> None:
    _, raw_key, factory = api

    with factory() as session:
        record = session.query(ApiKeyRecord).filter_by(name="Test client").one()

    assert record.key_digest != raw_key
    assert raw_key not in record.key_digest


def test_marks_persisted_job_failed_when_queue_is_unavailable(api) -> None:
    client, raw_key, _ = api

    def unavailable(_: str) -> None:
        raise ConnectionError("synthetic queue outage")

    app.dependency_overrides[get_job_dispatcher] = lambda: unavailable
    response = client.post(
        "/v1/jobs",
        headers={"X-API-Key": raw_key},
        data={"perfil": "organizacao", "toggles": "{}"},
        files=[
            ("fontes", ("fonte.txt", b"Conteudo sintetico suficientemente longo.", "text/plain"))
        ],
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "QUEUE_UNAVAILABLE"
    assert response.json()["error"]["details"]["job_id"]
