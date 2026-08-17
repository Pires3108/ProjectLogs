import time
from collections.abc import Callable

from app.analysis.models import AnalysisOutcome
from app.analysis.provider import AnalysisProvider, AnalysisProviderError
from app.errors import ApiError


class AnalysisService:
    def __init__(
        self,
        *,
        primary: AnalysisProvider,
        fallback: AnalysisProvider,
        max_attempts: int = 2,
        backoff_seconds: float = 1.0,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.max_attempts = max(1, max_attempts)
        self.backoff_seconds = max(0, backoff_seconds)
        self.sleeper = sleeper

    def analyze(self, text: str) -> AnalysisOutcome:
        failures: list[dict[str, str]] = []
        for provider, is_fallback in ((self.primary, False), (self.fallback, True)):
            for attempt in range(self.max_attempts):
                try:
                    analysis = provider.analyze(text)
                except AnalysisProviderError as exception:
                    failures.append({"provider": exception.provider, "reason": exception.reason})
                    if attempt + 1 < self.max_attempts:
                        self.sleeper(self.backoff_seconds * (2**attempt))
                    continue
                return AnalysisOutcome(
                    analise=analysis,
                    provedor=provider.name,
                    modelo=provider.model,
                    fallback_utilizado=is_fallback,
                )
        raise ApiError(
            status_code=503,
            code="LLM_PROVIDERS_UNAVAILABLE",
            message="Os provedores de análise estão indisponíveis.",
            details={"failures": failures},
        )
