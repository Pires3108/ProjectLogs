import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from app.transcription.provider import TranscriptionProviderError


class FfmpegAudioPreprocessor:
    """Produces small speech-optimized MP3 chunks accepted by free transcription APIs."""

    def __init__(
        self,
        *,
        binary: str = "ffmpeg",
        probe_binary: str = "ffprobe",
        chunk_seconds: int = 1200,
        max_duration_seconds: int = 3 * 60 * 60,
    ) -> None:
        self.binary = binary
        self.probe_binary = probe_binary
        self.chunk_seconds = chunk_seconds
        self.max_duration_seconds = max_duration_seconds

    def duration(self, source: Path) -> float:
        command = [
            self.probe_binary,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(source),
        ]
        try:
            result = subprocess.run(command, check=False, capture_output=True, timeout=30)
            duration = float(result.stdout.decode().strip())
        except (OSError, ValueError, subprocess.TimeoutExpired) as exception:
            raise TranscriptionProviderError("ffmpeg", "metadata_failed") from exception
        if result.returncode != 0 or duration <= 0:
            raise TranscriptionProviderError("ffmpeg", "metadata_failed")
        return duration

    @contextmanager
    def prepare(self, source: Path) -> Iterator[list[Path]]:
        if self.duration(source) > self.max_duration_seconds:
            raise TranscriptionProviderError("ffmpeg", "duration_exceeded")
        with TemporaryDirectory(prefix="ataviva-audio-") as directory:
            output_pattern = Path(directory) / "chunk-%04d.mp3"
            command = [
                self.binary,
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-map",
                "0:a:0",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-b:a",
                "32k",
                "-f",
                "segment",
                "-segment_time",
                str(self.chunk_seconds),
                "-reset_timestamps",
                "1",
                str(output_pattern),
            ]
            try:
                completed = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    timeout=max(300, self.chunk_seconds),
                )
            except (OSError, subprocess.TimeoutExpired) as exception:
                raise TranscriptionProviderError("ffmpeg", "preprocessing_failed") from exception
            chunks = sorted(Path(directory).glob("chunk-*.mp3"))
            if completed.returncode != 0 or not chunks:
                raise TranscriptionProviderError("ffmpeg", "preprocessing_failed")
            yield chunks
