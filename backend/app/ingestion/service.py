from pathlib import Path

from fastapi import UploadFile

from app.config import Settings
from app.errors import ApiError
from app.ingestion.normalizers import normalize_source
from app.ingestion.read_ai import parse_read_ai_transcript
from app.ingestion.storage import SourceStorage, create_source_storage
from app.ingestion.types import SUPPORTED_SOURCE_TYPES, SourceKind
from app.models import IngestedSource


def source_extension(filename: str | None) -> str:
    extension = Path(filename or "").suffix.lower()
    if extension not in SUPPORTED_SOURCE_TYPES:
        raise ApiError(
            status_code=400,
            code="UNSUPPORTED_FORMAT",
            message="O formato do arquivo não é suportado.",
            details={"filename": Path(filename or "sem-nome").name, "extension": extension},
        )
    return extension


def size_limit(extension: str, settings: Settings) -> int:
    kind = SUPPORTED_SOURCE_TYPES[extension].kind
    if kind is SourceKind.audio:
        return settings.max_audio_bytes
    if kind is SourceKind.video:
        return settings.max_video_bytes
    return settings.max_document_bytes


async def read_bounded(upload: UploadFile, limit: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while chunk := await upload.read(1024 * 1024):
        size += len(chunk)
        if size > limit:
            raise ApiError(
                status_code=413,
                code="FILE_TOO_LARGE",
                message="O arquivo excede o limite configurado.",
                details={"filename": Path(upload.filename or "sem-nome").name, "max_bytes": limit},
            )
        chunks.append(chunk)
    return b"".join(chunks)


async def ingest_upload(
    upload: UploadFile,
    settings: Settings,
    storage: SourceStorage | None = None,
) -> IngestedSource:
    extension = source_extension(upload.filename)
    source_type = SUPPORTED_SOURCE_TYPES[extension]
    content = await read_bounded(upload, size_limit(extension, settings))
    if not content:
        raise ApiError(
            status_code=422,
            code="INSUFFICIENT_CONTENT",
            message="O arquivo enviado está vazio.",
            details={"filename": Path(upload.filename or "sem-nome").name},
        )
    validate_binary_signature(extension, content)

    normalized_text = None
    reported_format = extension.removeprefix(".")
    if not source_type.needs_transcription:
        if extension == ".txt":
            try:
                read_ai = parse_read_ai_transcript(content)
            except ApiError:
                normalized_text = normalize_source(extension, content)
            else:
                normalized_text = read_ai.texto_normalizado
                reported_format = "read.ai"
        else:
            normalized_text = normalize_source(extension, content)
        if len(normalized_text) < settings.minimum_text_characters:
            raise ApiError(
                status_code=422,
                code="INSUFFICIENT_CONTENT",
                message="O arquivo não contém texto suficiente para análise.",
                details={"filename": Path(upload.filename or "sem-nome").name},
            )

    source_id = (storage or create_source_storage(settings)).save(extension, content)
    return IngestedSource(
        id=source_id,
        nome=Path(upload.filename or f"fonte{extension}").name,
        formato=reported_format,
        tipo=source_type.kind,
        tamanho_bytes=len(content),
        requer_transcricao=source_type.needs_transcription,
        texto_normalizado=normalized_text,
    )


def validate_binary_signature(extension: str, content: bytes) -> None:
    valid = True
    if extension == ".wav":
        valid = len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WAVE"
    elif extension == ".mp3":
        valid = content.startswith(b"ID3") or (
            len(content) >= 2 and content[0] == 0xFF and content[1] & 0xE0 == 0xE0
        )
    elif extension in {".mp4", ".mov"}:
        valid = len(content) >= 12 and content[4:8] == b"ftyp"
    if not valid:
        raise ApiError(
            status_code=400,
            code="INVALID_FILE_CONTENT",
            message="O conteúdo do arquivo não corresponde ao formato informado.",
            details={"extension": extension},
        )
