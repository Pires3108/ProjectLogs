from pathlib import Path

from app.config import get_settings
from app.db.base import Base
from app.db.models import ApiKeyRecord, JobRecord
from app.db.session import get_engine, get_session_factory
from app.jobs.storage import DatabaseHtmlStorage


def test_database_html_storage_survives_local_filesystem_loss(tmp_path: Path, monkeypatch) -> None:
    database = tmp_path / "html-storage.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database.as_posix()}")
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    try:
        Base.metadata.create_all(get_engine())
        with get_session_factory()() as session:
            key = ApiKeyRecord(
                id="00000000-0000-0000-0000-000000000001",
                name="synthetic",
                key_prefix="ataviva_test",
                key_digest="0" * 64,
            )
            job = JobRecord(
                id="00000000-0000-0000-0000-000000000002",
                api_key_id=key.id,
                perfil="estudo",
                toggles={},
                warnings=[],
            )
            session.add_all([key, job])
            session.commit()

        storage = DatabaseHtmlStorage()
        storage_key = storage.save(job.id, "<!doctype html><title>AtaViva</title>")

        assert storage_key == f"database/{job.id}.html"
        assert storage.load(storage_key).decode().startswith("<!doctype html>")
        storage.delete(storage_key)
    finally:
        get_session_factory.cache_clear()
        get_engine.cache_clear()
        get_settings.cache_clear()
