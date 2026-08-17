from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class JobStatus(StrEnum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"


class ApiKeyRecord(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    key_digest: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    jobs: Mapped[list["JobRecord"]] = relationship(back_populates="api_key")


class JobRecord(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    api_key_id: Mapped[str] = mapped_column(ForeignKey("api_keys.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.queued, index=True)
    perfil: Mapped[str] = mapped_column(String(30), nullable=False)
    toggles: Mapped[dict] = mapped_column(JSON, nullable=False)
    warnings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    llm_provider: Mapped[str | None] = mapped_column(String(40))
    analysis_data: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[dict | None] = mapped_column(JSON)
    html_storage_key: Mapped[str | None] = mapped_column(String(500))
    html_content: Mapped[str | None] = mapped_column(Text)

    api_key: Mapped[ApiKeyRecord] = relationship(back_populates="jobs")
    sources: Mapped[list["SourceRecord"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class SourceRecord(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    extension: Mapped[str] = mapped_column(String(20), nullable=False)
    format: Mapped[str] = mapped_column(String(30), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    requires_transcription: Mapped[bool] = mapped_column(Boolean, nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text)

    job: Mapped[JobRecord] = relationship(back_populates="sources")
