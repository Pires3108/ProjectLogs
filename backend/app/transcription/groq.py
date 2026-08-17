from pathlib import Path

import httpx

from app.transcription.audio import FfmpegAudioPreprocessor
from app.transcription.models import TranscriptionResult, TranscriptSegment
from app.transcription.provider import TranscriptionProviderError


class GroqTranscriptionProvider:
    name = "groq"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        url: str,
        preprocessor: FfmpegAudioPreprocessor,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.url = url
        self.preprocessor = preprocessor
        self.client = client or httpx.Client(timeout=120)

    def transcribe(self, source: Path) -> TranscriptionResult:
        texts: list[str] = []
        segments: list[TranscriptSegment] = []
        duration = 0.0
        with self.preprocessor.prepare(source) as chunks:
            for index, chunk in enumerate(chunks):
                payload = self._transcribe_chunk(chunk)
                chunk_offset = index * self.preprocessor.chunk_seconds
                chunk_text = str(payload.get("text", "")).strip()
                if chunk_text:
                    texts.append(chunk_text)
                for item in payload.get("segments", []):
                    text = str(item.get("text", "")).strip()
                    if not text:
                        continue
                    start = chunk_offset + float(item["start"])
                    end = chunk_offset + float(item["end"])
                    segments.append(
                        TranscriptSegment(
                            inicio_segundos=start,
                            fim_segundos=end,
                            texto=text,
                        )
                    )
                    duration = max(duration, end)
        return TranscriptionResult(
            texto="\n".join(texts),
            idioma=None,
            duracao_segundos=duration or None,
            segmentos=segments,
            provedor=self.name,
            modelo=self.model,
        )

    def _transcribe_chunk(self, chunk: Path) -> dict:
        try:
            with chunk.open("rb") as audio:
                response = self.client.post(
                    self.url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data={
                        "model": self.model,
                        "response_format": "verbose_json",
                        "timestamp_granularities[]": "segment",
                    },
                    files={"file": (chunk.name, audio, "audio/mpeg")},
                )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exception:
            raise TranscriptionProviderError(
                self.name, f"http_{exception.response.status_code}"
            ) from exception
        except (httpx.HTTPError, ValueError) as exception:
            raise TranscriptionProviderError(self.name, "request_failed") from exception
