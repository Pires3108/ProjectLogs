import subprocess
from pathlib import Path

import pytest

from app.transcription.audio import FfmpegAudioPreprocessor
from app.transcription.provider import TranscriptionProviderError


def test_reads_media_duration_with_ffprobe(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "meeting.mp4"
    source.write_bytes(b"synthetic")

    def run(command, **kwargs):
        assert command[0] == "custom-ffprobe"
        assert command[-1] == str(source)
        return subprocess.CompletedProcess(command, 0, stdout=b"2275.25\n", stderr=b"")

    monkeypatch.setattr(subprocess, "run", run)
    preprocessor = FfmpegAudioPreprocessor(probe_binary="custom-ffprobe")

    assert preprocessor.duration(source) == 2275.25


def test_rejects_media_above_configured_duration(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "meeting.mp4"
    source.write_bytes(b"synthetic")
    preprocessor = FfmpegAudioPreprocessor(max_duration_seconds=10)
    monkeypatch.setattr(preprocessor, "duration", lambda _: 11)

    with pytest.raises(TranscriptionProviderError) as captured:
        with preprocessor.prepare(source):
            pass

    assert captured.value.reason == "duration_exceeded"
