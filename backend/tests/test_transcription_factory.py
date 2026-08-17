import pytest

from app.config import Settings
from app.errors import ApiError
from app.transcription.factory import create_transcription_service


def test_requires_groq_key_to_create_transcription_service() -> None:
    with pytest.raises(ApiError) as captured:
        create_transcription_service(Settings(groq_api_key=None))

    assert captured.value.code == "TRANSCRIPTION_NOT_CONFIGURED"


def test_builds_groq_service_from_configuration() -> None:
    service = create_transcription_service(Settings(groq_api_key="synthetic-secret"))

    assert service.provider.name == "groq"
