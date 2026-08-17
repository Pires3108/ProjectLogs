import pytest

from app.analysis.models import StructuredAnalysis
from app.analysis.provider import AnalysisProviderError
from app.analysis.service import AnalysisService
from app.errors import ApiError
from tests.analysis_fixtures import VALID_ANALYSIS


class StubProvider:
    def __init__(self, name: str, responses: list[StructuredAnalysis | Exception]) -> None:
        self.name = name
        self.model = f"{name}-model"
        self.responses = responses
        self.calls = 0

    def analyze(self, text: str) -> StructuredAnalysis:
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def analysis() -> StructuredAnalysis:
    return StructuredAnalysis.model_validate(VALID_ANALYSIS)


def test_returns_primary_without_calling_fallback() -> None:
    primary = StubProvider("gemini", [analysis()])
    fallback = StubProvider("groq", [analysis()])
    service = AnalysisService(primary=primary, fallback=fallback, sleeper=lambda _: None)

    outcome = service.analyze("fonte sintética")

    assert outcome.provedor == "gemini"
    assert outcome.fallback_utilizado is False
    assert fallback.calls == 0


def test_retries_primary_then_falls_back_on_429() -> None:
    delays: list[float] = []
    primary = StubProvider(
        "gemini",
        [
            AnalysisProviderError("gemini", "http_429", status_code=429),
            AnalysisProviderError("gemini", "http_429", status_code=429),
        ],
    )
    fallback = StubProvider("groq", [analysis()])
    service = AnalysisService(
        primary=primary,
        fallback=fallback,
        max_attempts=2,
        backoff_seconds=0.5,
        sleeper=delays.append,
    )

    outcome = service.analyze("fonte sintética")

    assert outcome.provedor == "groq"
    assert outcome.fallback_utilizado is True
    assert primary.calls == 2
    assert delays == [0.5]


def test_returns_503_after_both_providers_fail() -> None:
    primary = StubProvider("gemini", [AnalysisProviderError("gemini", "request_failed")])
    fallback = StubProvider("groq", [AnalysisProviderError("groq", "request_failed")])
    service = AnalysisService(
        primary=primary,
        fallback=fallback,
        max_attempts=1,
        sleeper=lambda _: None,
    )

    with pytest.raises(ApiError) as captured:
        service.analyze("fonte sintética")

    assert captured.value.status_code == 503
    assert captured.value.code == "LLM_PROVIDERS_UNAVAILABLE"
    assert captured.value.details["failures"] == [
        {"provider": "gemini", "reason": "request_failed"},
        {"provider": "groq", "reason": "request_failed"},
    ]
