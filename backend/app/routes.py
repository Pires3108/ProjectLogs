from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.config import get_settings
from app.documents.configuration import (
    PROFILE_RULES,
    DocumentConfiguration,
    ValidatedConfiguration,
    validate_configuration,
)
from app.errors import ApiError
from app.ingestion.service import ingest_upload
from app.ingestion.storage import create_source_storage
from app.models import (
    CapabilitiesResponse,
    HealthResponse,
    IngestionResponse,
    ProfileDefinition,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["sistema"], operation_id="health")
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name, version=settings.app_version)


@router.get(
    "/v1/capabilities",
    response_model=CapabilitiesResponse,
    tags=["configuração"],
    operation_id="capabilities",
)
async def capabilities() -> CapabilitiesResponse:
    return CapabilitiesResponse(
        perfis=[
            ProfileDefinition(
                perfil=profile,
                toggles_permitidos=sorted(rules.toggles_permitidos),
                secoes_obrigatorias=rules.secoes_obrigatorias,
                foco=rules.foco,
            )
            for profile, rules in PROFILE_RULES.items()
        ],
        formatos_planejados_v1=[
            "read.ai",
            "mp3",
            "wav",
            "mp4",
            "mov",
            "txt",
            "vtt",
            "srt",
            "md",
            "docx",
        ],
    )


@router.post(
    "/v1/document-configurations/validate",
    response_model=ValidatedConfiguration,
    tags=["configuração"],
    operation_id="validate_document_configuration",
)
async def validate_document_configuration(
    configuration: DocumentConfiguration,
) -> ValidatedConfiguration:
    return validate_configuration(configuration)


@router.post(
    "/v1/ingestions",
    response_model=IngestionResponse,
    status_code=201,
    tags=["ingestão"],
    operation_id="create_ingestion",
)
async def create_ingestion(
    fontes: Annotated[list[UploadFile], File(description="Uma ou mais fontes da reunião")],
) -> IngestionResponse:
    if not fontes:
        raise ApiError(
            status_code=422,
            code="INSUFFICIENT_CONTENT",
            message="Envie ao menos uma fonte para análise.",
        )
    settings = get_settings()
    storage = create_source_storage(settings)
    ingested = [await ingest_upload(source, settings, storage) for source in fontes]
    return IngestionResponse(
        fontes=ingested,
        total_fontes=len(ingested),
        pronto_para_analise=all(not source.requer_transcricao for source in ingested),
    )
