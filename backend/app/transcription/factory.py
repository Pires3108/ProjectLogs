from app.config import Settings
from app.errors import ApiError
from app.ingestion.storage import create_source_storage
from app.transcription.audio import FfmpegAudioPreprocessor
from app.transcription.groq import GroqTranscriptionProvider
from app.transcription.service import TranscriptionService


def create_transcription_service(settings: Settings) -> TranscriptionService:
    if settings.groq_api_key is None or not settings.groq_api_key.get_secret_value():
        raise ApiError(
            status_code=503,
            code="TRANSCRIPTION_NOT_CONFIGURED",
            message="O serviço de transcrição não está configurado.",
        )
    preprocessor = FfmpegAudioPreprocessor(
        binary=settings.ffmpeg_binary,
        probe_binary=settings.ffprobe_binary,
        chunk_seconds=settings.transcription_chunk_seconds,
        max_duration_seconds=settings.max_media_duration_seconds,
    )
    provider = GroqTranscriptionProvider(
        api_key=settings.groq_api_key.get_secret_value(),
        model=settings.groq_transcription_model,
        url=settings.groq_transcription_url,
        preprocessor=preprocessor,
    )
    return TranscriptionService(
        storage=create_source_storage(settings),
        provider=provider,
    )
