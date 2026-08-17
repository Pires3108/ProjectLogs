from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth.keys import ApiPrincipal
from app.config import get_settings
from app.db.models import JobRecord, SourceRecord
from app.errors import ApiError
from app.jobs.schemas import JobResponse, JobSourceResponse


def get_owned_job(session: Session, principal: ApiPrincipal, job_id: str) -> JobRecord:
    job = session.scalar(
        select(JobRecord)
        .options(selectinload(JobRecord.sources))
        .where(JobRecord.id == job_id, JobRecord.api_key_id == principal.id)
    )
    if job is None:
        raise ApiError(
            status_code=404,
            code="JOB_NOT_FOUND",
            message="O job solicitado não foi encontrado.",
        )
    return job


def job_response(job: JobRecord, queue_position: int | None = None) -> JobResponse:
    return JobResponse(
        id=job.id,
        status=job.status,
        perfil=job.perfil,
        toggles=job.toggles,
        avisos=job.warnings,
        fontes=[
            JobSourceResponse(
                id=source.id,
                nome=source.original_name,
                formato=source.format,
                tipo=source.kind,
                tamanho_bytes=source.size_bytes,
                requer_transcricao=source.requires_transcription,
            )
            for source in job.sources
        ],
        provedor_llm=job.llm_provider,
        analise=job.analysis_data,
        erro=job.error,
        html_url=f"/v1/jobs/{job.id}/html" if job.html_storage_key else None,
        criado_em=job.created_at,
        atualizado_em=job.updated_at,
        fila_posicao=queue_position,
        fila_estimativa_minutos=(
            queue_position * get_settings().estimated_job_minutes if queue_position else None
        ),
    )


def get_queue_position(session: Session, job: JobRecord) -> int | None:
    if job.status != "queued":
        return None
    ahead = session.scalar(
        select(func.count(JobRecord.id)).where(
            JobRecord.status.in_(["queued", "processing"]),
            JobRecord.created_at <= job.created_at,
        )
    )
    return int(ahead or 0)


def source_record(job_id: str, source) -> SourceRecord:
    original_extension = Path(source.nome).suffix.lower()
    return SourceRecord(
        id=source.id,
        job_id=job_id,
        original_name=source.nome,
        extension=original_extension,
        format=source.formato,
        kind=source.tipo,
        size_bytes=source.tamanho_bytes,
        requires_transcription=source.requer_transcricao,
        normalized_text=source.texto_normalizado,
    )
