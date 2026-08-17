from pathlib import Path

import pytest

from app.errors import ApiError
from app.ingestion.storage import LocalSourceStorage
from app.transcription.models import TranscriptionResult, TranscriptSegment
from app.transcription.provider import TranscriptionProviderError
from app.transcription.service import TranscriptionService


class StubTranscriber:
    name = "stub"

    def transcribe(self, source: Path) -> TranscriptionResult:
        assert source.read_bytes() == b"synthetic audio"
        return TranscriptionResult(
            texto="Decidimos publicar a primeira versão.",
            idioma="pt-BR",
            duracao_segundos=3,
            segmentos=[
                TranscriptSegment(
                    inicio_segundos=0,
                    fim_segundos=3,
                    texto="Decidimos publicar a primeira versão.",
                )
            ],
            provedor=self.name,
            modelo="stub-v1",
        )


class FailingTranscriber:
    name = "failing-stub"

    def transcribe(self, source: Path) -> TranscriptionResult:
        raise TranscriptionProviderError(self.name, "quota")


class TooLongTranscriber:
    name = "ffmpeg"

    def transcribe(self, source: Path) -> TranscriptionResult:
        raise TranscriptionProviderError(self.name, "duration_exceeded")


def test_transcribes_stored_media_without_provider_coupling(tmp_path: Path) -> None:
    storage = LocalSourceStorage(str(tmp_path))
    source_id = storage.save(".mp3", b"synthetic audio")
    service = TranscriptionService(storage=storage, provider=StubTranscriber())

    result = service.transcribe(source_id, ".mp3")

    assert result.provedor == "stub"
    assert result.segmentos[0].fim_segundos == 3


def test_rejects_transcription_for_text_source(tmp_path: Path) -> None:
    storage = LocalSourceStorage(str(tmp_path))
    source_id = storage.save(".txt", b"synthetic transcript")
    service = TranscriptionService(storage=storage, provider=StubTranscriber())

    with pytest.raises(ApiError) as captured:
        service.transcribe(source_id, ".txt")

    assert captured.value.code == "TRANSCRIPTION_NOT_REQUIRED"


def test_maps_provider_failure_without_leaking_source_content(tmp_path: Path) -> None:
    storage = LocalSourceStorage(str(tmp_path))
    source_id = storage.save(".wav", b"synthetic audio")
    service = TranscriptionService(storage=storage, provider=FailingTranscriber())

    with pytest.raises(ApiError) as captured:
        service.transcribe(source_id, ".wav")

    assert captured.value.status_code == 503
    assert captured.value.details == {"provider": "failing-stub", "reason": "quota"}


def test_maps_duration_limit_to_validation_error(tmp_path: Path) -> None:
    storage = LocalSourceStorage(str(tmp_path))
    source_id = storage.save(".mp3", b"synthetic audio")
    service = TranscriptionService(storage=storage, provider=TooLongTranscriber())

    with pytest.raises(ApiError) as captured:
        service.transcribe(source_id, ".mp3")

    assert captured.value.status_code == 422
    assert captured.value.code == "MEDIA_DURATION_EXCEEDED"
