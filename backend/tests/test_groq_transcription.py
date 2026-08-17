from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import httpx

from app.transcription.groq import GroqTranscriptionProvider


class StubPreprocessor:
    chunk_seconds = 1200

    def __init__(self, chunks: list[Path]) -> None:
        self.chunks = chunks

    @contextmanager
    def prepare(self, source: Path) -> Iterator[list[Path]]:
        assert source.name == "meeting.mp4"
        yield self.chunks


def test_combines_groq_chunks_and_offsets_segments(tmp_path: Path) -> None:
    first = tmp_path / "chunk-0000.mp3"
    second = tmp_path / "chunk-0001.mp3"
    first.write_bytes(b"first synthetic chunk")
    second.write_bytes(b"second synthetic chunk")
    responses = [
        {
            "text": "Primeira parte.",
            "segments": [{"start": 0, "end": 3, "text": "Primeira parte."}],
        },
        {
            "text": "Segunda parte.",
            "segments": [{"start": 1, "end": 4, "text": "Segunda parte."}],
        },
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(200, json=responses.pop(0))

    provider = GroqTranscriptionProvider(
        api_key="test-key",
        model="whisper-large-v3-turbo",
        url="https://groq.invalid/transcriptions",
        preprocessor=StubPreprocessor([first, second]),  # type: ignore[arg-type]
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = provider.transcribe(tmp_path / "meeting.mp4")

    assert result.texto == "Primeira parte.\nSegunda parte."
    assert result.segmentos[1].inicio_segundos == 1201
    assert result.duracao_segundos == 1204
