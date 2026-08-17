import time
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.keys import ApiPrincipal
from app.auth.rate_limit import require_rate_limited_api_key
from app.config import get_settings
from app.errors import ApiError
from app.ingestion.service import size_limit, source_extension
from app.ingestion.storage import create_source_storage
from app.ingestion.tickets import UploadTicket, sign_ticket
from app.ingestion.types import SUPPORTED_SOURCE_TYPES

router = APIRouter(prefix="/v1/uploads", tags=["uploads"])


class UploadRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    tamanho_bytes: int = Field(gt=0)
    content_type: str | None = None


class UploadResponse(BaseModel):
    upload_url: str
    metodo: str = "PUT"
    headers: dict[str, str]
    ticket: str
    expira_em: int


@router.post("", response_model=UploadResponse, operation_id="create_direct_upload")
def create_direct_upload(
    request: UploadRequest,
    principal: Annotated[ApiPrincipal, Depends(require_rate_limited_api_key)],
) -> UploadResponse:
    settings = get_settings()
    if settings.storage_backend != "s3":
        raise ApiError(
            status_code=503,
            code="DIRECT_UPLOAD_UNAVAILABLE",
            message="O upload direto exige armazenamento S3/R2.",
        )
    safe_name = Path(request.nome).name
    extension = source_extension(safe_name)
    maximum = size_limit(extension, settings)
    if request.tamanho_bytes > maximum:
        raise ApiError(
            status_code=413,
            code="FILE_TOO_LARGE",
            message="O arquivo excede o limite configurado.",
            details={"max_bytes": maximum},
        )
    source_type = SUPPORTED_SOURCE_TYPES[extension]
    content_type = request.content_type or source_type.media_type
    source_id = str(uuid4())
    expires_at = int(time.time()) + settings.direct_upload_expiry_seconds
    ticket = UploadTicket(
        source_id,
        principal.id,
        safe_name,
        extension,
        content_type,
        request.tamanho_bytes,
        expires_at,
    )
    storage = create_source_storage(settings)
    url = storage.create_upload(
        source_id, extension, content_type, settings.direct_upload_expiry_seconds
    )
    return UploadResponse(
        upload_url=url,
        headers={"Content-Type": content_type},
        ticket=sign_ticket(ticket, settings.api_key_pepper.get_secret_value()),
        expira_em=expires_at,
    )
