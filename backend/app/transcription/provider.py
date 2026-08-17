from pathlib import Path
from typing import Protocol

from app.transcription.models import TranscriptionResult


class TranscriptionProvider(Protocol):
    @property
    def name(self) -> str: ...

    def transcribe(self, source: Path) -> TranscriptionResult: ...


class TranscriptionProviderError(Exception):
    def __init__(self, provider: str, reason: str) -> None:
        self.provider = provider
        self.reason = reason
        super().__init__(f"Transcription provider {provider} failed: {reason}")
