from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.keys import ApiPrincipal
from app.auth.rate_limit import require_rate_limited_api_key
from app.config import get_settings
from app.db.models import JobRecord, SourceRecord
from app.db.session import get_db_session
from app.documents.configuration import (
    ContentToggles,
    DocumentConfiguration,
    validate_configuration,
)
from app.errors import ApiError
from app.ingestion.service import ingest_upload
from app.ingestion.storage import create_source_storage
from app.ingestion.tickets import verify_ticket
from app.ingestion.types import SUPPORTED_SOURCE_TYPES
from app.jobs.dispatch import JobDispatcher, get_job_dispatcher
from app.jobs.schemas import DirectJobRequest, JobResponse
from app.jobs.service import get_owned_job, get_queue_position, job_response, source_record
from app.jobs.storage import create_html_storage
from app.models import DocumentProfile, IngestedSource

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


def dispatch_persisted_job(session: Session, dispatch: JobDispatcher, job: JobRecord) -> None:
    try:
        dispatch(job.id)
    except Exception as exception:
        job.status = "failed"
        job.error = {
            "code": "QUEUE_UNAVAILABLE",
            "message": "A fila de processamento está indisponível.",
            "details": {},
        }
        session.commit()
        raise ApiError(
            status_code=503,
            code="QUEUE_UNAVAILABLE",
            message="A fila de processamento está indisponível.",
            details={"job_id": job.id},
        ) from exception


@router.post("", response_model=JobResponse, status_code=202, operation_id="create_job")
async def create_job(
    perfil: Annotated[DocumentProfile, Form()],
    toggles: Annotated[str, Form(description="Objeto JSON com os toggles")],
    fontes: Annotated[list[UploadFile], File()],
    principal: Annotated[ApiPrincipal, Depends(require_rate_limited_api_key)],
    session: Annotated[Session, Depends(get_db_session)],
    dispatch: Annotated[JobDispatcher, Depends(get_job_dispatcher)],
) -> JobResponse:
    try:
        parsed_toggles = ContentToggles.model_validate_json(toggles)
    except ValidationError as exception:
        raise ApiError(
            status_code=422,
            code="INVALID_TOGGLES",
            message="O campo toggles não contém um objeto JSON válido.",
            details={"errors": exception.errors(include_input=False)},
        ) from exception
    configuration = validate_configuration(
        DocumentConfiguration(perfil=perfil, toggles=parsed_toggles)
    )
    settings = get_settings()
    storage = create_source_storage(settings)
    ingested = []
    try:
        for upload in fontes:
            ingested.append(await ingest_upload(upload, settings, storage))
        job = JobRecord(
            api_key_id=principal.id,
            perfil=configuration.perfil,
            toggles=configuration.toggles.model_dump(mode="json"),
            warnings=[warning.model_dump(mode="json") for warning in configuration.avisos],
        )
        session.add(job)
        session.flush()
        session.add_all([source_record(job.id, source) for source in ingested])
        session.commit()
    except Exception:
        session.rollback()
        for source in ingested:
            storage.delete(source.id, Path(source.nome).suffix.lower())
        raise
    dispatch_persisted_job(session, dispatch, job)
    persisted = get_owned_job(session, principal, job.id)
    return job_response(persisted, get_queue_position(session, persisted))


@router.post(
    "/from-uploads",
    response_model=JobResponse,
    status_code=202,
    operation_id="create_job_from_uploads",
)
def create_job_from_uploads(
    request: DirectJobRequest,
    principal: Annotated[ApiPrincipal, Depends(require_rate_limited_api_key)],
    session: Annotated[Session, Depends(get_db_session)],
    dispatch: Annotated[JobDispatcher, Depends(get_job_dispatcher)],
) -> JobResponse:
    if not request.tickets:
        raise ApiError(
            status_code=422, code="NO_SOURCES", message="Informe ao menos um ticket de upload."
        )
    settings = get_settings()
    storage = create_source_storage(settings)
    tickets = [
        verify_ticket(value, settings.api_key_pepper.get_secret_value())
        for value in request.tickets
    ]
    if len({ticket.source_id for ticket in tickets}) != len(tickets):
        raise ApiError(
            status_code=400,
            code="DUPLICATE_UPLOAD",
            message="Um mesmo upload foi informado mais de uma vez.",
        )
    attached_source = session.scalar(
        select(SourceRecord.id).where(SourceRecord.id.in_([ticket.source_id for ticket in tickets]))
    )
    if attached_source is not None:
        raise ApiError(
            status_code=409,
            code="UPLOAD_ALREADY_USED",
            message="Um dos tickets de upload já foi usado em outro job.",
        )
    for ticket in tickets:
        if ticket.api_key_id != principal.id:
            raise ApiError(
                status_code=404,
                code="UPLOAD_NOT_FOUND",
                message="O upload solicitado não foi encontrado.",
            )
        if storage.size(ticket.source_id, ticket.extension) != ticket.size_bytes:
            raise ApiError(
                status_code=422,
                code="UPLOAD_SIZE_MISMATCH",
                message="O tamanho armazenado não corresponde ao ticket.",
            )
    configuration = validate_configuration(
        DocumentConfiguration(perfil=request.perfil, toggles=request.toggles)
    )
    job = JobRecord(
        api_key_id=principal.id,
        perfil=configuration.perfil,
        toggles=configuration.toggles.model_dump(mode="json"),
        warnings=[warning.model_dump(mode="json") for warning in configuration.avisos],
    )
    session.add(job)
    session.flush()
    for ticket in tickets:
        source_type = SUPPORTED_SOURCE_TYPES[ticket.extension]
        source = IngestedSource(
            id=ticket.source_id,
            nome=ticket.filename,
            formato=ticket.extension.removeprefix("."),
            tipo=source_type.kind,
            tamanho_bytes=ticket.size_bytes,
            requer_transcricao=source_type.needs_transcription,
        )
        session.add(source_record(job.id, source))
    session.commit()
    dispatch_persisted_job(session, dispatch, job)
    persisted = get_owned_job(session, principal, job.id)
    return job_response(persisted, get_queue_position(session, persisted))


@router.get("/{job_id}", response_model=JobResponse, operation_id="get_job")
def get_job(
    job_id: str,
    principal: Annotated[ApiPrincipal, Depends(require_rate_limited_api_key)],
    session: Annotated[Session, Depends(get_db_session)],
) -> JobResponse:
    job = get_owned_job(session, principal, job_id)
    return job_response(job, get_queue_position(session, job))


@router.get(
    "/{job_id}/html",
    response_class=Response,
    operation_id="download_job_html",
)
def download_job_html(
    job_id: str,
    principal: Annotated[ApiPrincipal, Depends(require_rate_limited_api_key)],
    session: Annotated[Session, Depends(get_db_session)],
) -> Response:
    job = get_owned_job(session, principal, job_id)
    if not job.html_storage_key:
        raise ApiError(
            status_code=409,
            code="JOB_NOT_READY",
            message="O HTML ainda não está disponível.",
            details={"status": job.status},
        )
    content = create_html_storage(get_settings()).load(job.html_storage_key)
    return Response(
        content=content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="ataviva-{job.id}.html"'},
    )
