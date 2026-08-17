import pytest

from app.analysis.factory import create_analysis_service
from app.config import Settings
from app.errors import ApiError


def test_requires_both_analysis_provider_keys() -> None:
    with pytest.raises(ApiError) as captured:
        create_analysis_service(Settings(gemini_api_key=None, groq_api_key="synthetic"))

    assert captured.value.code == "LLM_NOT_CONFIGURED"


def test_configures_gemini_primary_and_groq_fallback() -> None:
    service = create_analysis_service(
        Settings(gemini_api_key="synthetic-gemini", groq_api_key="synthetic-groq")
    )

    assert service.primary.name == "gemini"
    assert service.primary.model == "gemini-3.6-flash"
    assert service.fallback.name == "groq"


def test_replaces_retired_gemini_model_from_environment() -> None:
    settings = Settings(gemini_analysis_model="gemini-2.5-flash")

    assert settings.gemini_analysis_model == "gemini-3.6-flash"
