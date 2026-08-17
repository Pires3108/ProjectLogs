from typing import Protocol

from app.analysis.models import StructuredAnalysis


class AnalysisProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def model(self) -> str: ...

    def analyze(self, text: str) -> StructuredAnalysis: ...


class AnalysisProviderError(Exception):
    def __init__(self, provider: str, reason: str, *, status_code: int | None = None) -> None:
        self.provider = provider
        self.reason = reason
        self.status_code = status_code
        super().__init__(f"Analysis provider {provider} failed: {reason}")
