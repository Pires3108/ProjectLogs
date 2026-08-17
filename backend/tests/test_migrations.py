from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import Settings, get_settings


def test_initial_migration_creates_required_tables(tmp_path: Path, monkeypatch) -> None:
    database = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database.as_posix()}")
    monkeypatch.setenv("DATABASE_URL_UNPOOLED", f"sqlite:///{database.as_posix()}")
    get_settings.cache_clear()
    configuration = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    try:
        command.upgrade(configuration, "head")
        inspector = inspect(create_engine(f"sqlite:///{database.as_posix()}"))
        tables = set(inspector.get_table_names())
        job_columns = {column["name"] for column in inspector.get_columns("jobs")}
    finally:
        get_settings.cache_clear()

    assert {"api_keys", "jobs", "sources", "alembic_version"} <= tables
    assert "analysis_data" in job_columns
    assert "html_content" in job_columns


def test_neon_urls_use_psycopg_and_direct_connection_for_migrations() -> None:
    settings = Settings(
        database_url="postgresql://user@host-pooler/db",
        database_url_unpooled="postgresql://user@host/db",
    )

    assert "-pooler" in settings.database_url
    assert "-pooler" not in settings.database_url_unpooled
