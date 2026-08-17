import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.analysis.factory import create_analysis_service
from app.config import get_settings
from app.db.models import JobRecord, JobStatus
from app.db.session import get_session_factory
from app.documents.html import HtmlGenerator
from app.errors import ApiError
from app.ingestion.storage import create_source_storage
from app.jobs.celery_app import celery_app
from app.jobs.processor import JobProcessor
from app.jobs.storage import create_html_storage
from app.observability import JOBS_PROCESSED
from app.transcription.factory import create_transcription_service

logger = logging.getLogger("ataviva.jobs")


@celery_app.task(name="ataviva.process_job")
def process_job(job_id: str) -> None:
    factory = get_session_factory()
    with factory() as session:
        job = session.scalar(
            select(JobRecord).options(selectinload(JobRecord.sources)).where(JobRecord.id == job_id)
        )
        if job is None or job.status != JobStatus.queued:
            return
        job.status = JobStatus.processing
        session.commit()
        logger.info(
            "job_processing_started",
            extra={"job_id": job.id, "perfil": job.perfil, "toggles": job.toggles},
        )
        try:
            settings = get_settings()
            processor = JobProcessor(
                analysis_service=create_analysis_service(settings),
                transcription_service=(
                    create_transcription_service(settings)
                    if any(source.requires_transcription for source in job.sources)
                    else None
                ),
                html_generator=HtmlGenerator(mermaid_asset_path=settings.mermaid_asset_path),
                html_storage=create_html_storage(settings),
                source_storage=create_source_storage(settings),
                minimum_text_characters=settings.minimum_text_characters,
            )
            processor.process(job)
            job.status = JobStatus.done
            job.error = None
            logger.info(
                "job_processing_completed",
                extra={
                    "job_id": job.id,
                    "perfil": job.perfil,
                    "toggles": job.toggles,
                    "provider": job.llm_provider,
                },
            )
            JOBS_PROCESSED.labels("done").inc()
        except ApiError as exception:
            job.status = JobStatus.failed
            job.error = {
                "code": exception.code,
                "message": exception.message,
                "details": exception.details,
            }
            logger.warning(
                "job_processing_failed",
                extra={"job_id": job.id, "perfil": job.perfil, "error_code": exception.code},
            )
            JOBS_PROCESSED.labels("failed").inc()
        except Exception:
            job.status = JobStatus.failed
            job.error = {
                "code": "INTERNAL_PROCESSING_ERROR",
                "message": "O job falhou durante o processamento.",
                "details": {},
            }
            logger.exception(
                "job_processing_failed",
                extra={
                    "job_id": job.id,
                    "perfil": job.perfil,
                    "error_code": "INTERNAL_PROCESSING_ERROR",
                },
            )
            JOBS_PROCESSED.labels("failed").inc()
        session.commit()


def enqueue_job(job_id: str) -> None:
    process_job.delay(job_id)
