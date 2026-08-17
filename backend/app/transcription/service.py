from app.errors import ApiError
from app.ingestion.storage import SourceStorage
from app.ingestion.types import SUPPORTED_SOURCE_TYPES
from app.transcription.models import TranscriptionResult
from app.transcription.provider import TranscriptionProvider, TranscriptionProviderError


class TranscriptionService:
    def __init__(self, *, storage: SourceStorage, provider: TranscriptionProvider) -> None:
        self.storage = storage
        self.provider = provider

    def transcribe(self, source_id: str, extension: str) -> TranscriptionResult:
        source_type = SUPPORTED_SOURCE_TYPES.get(extension)
        if source_type is None or not source_type.needs_transcription:
            raise ApiError(
                status_code=422,
                code="TRANSCRIPTION_NOT_REQUIRED",
                message="A fonte informada não requer transcrição.",
                details={"extension": extension},
            )
        with self.storage.materialize(source_id, extension) as source:
            try:
                result = self.provider.transcribe(source)
            except TranscriptionProviderError as exception:
                if exception.reason == "duration_exceeded":
                    raise ApiError(
                        status_code=422,
                        code="MEDIA_DURATION_EXCEEDED",
                        message="A duração da mídia excede o limite configurado.",
                    ) from exception
                raise ApiError(
                    status_code=503,
                    code="TRANSCRIPTION_UNAVAILABLE",
                    message="O serviço de transcrição está indisponível.",
                    details={"provider": exception.provider, "reason": exception.reason},
                ) from exception
        if not result.texto.strip():
            raise ApiError(
                status_code=422,
                code="INSUFFICIENT_CONTENT",
                message="A transcrição não produziu conteúdo suficiente.",
                details={"provider": result.provedor},
            )
        return result
