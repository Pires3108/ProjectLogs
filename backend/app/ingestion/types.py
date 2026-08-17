from dataclasses import dataclass
from enum import StrEnum


class SourceKind(StrEnum):
    document = "document"
    transcript = "transcript"
    audio = "audio"
    video = "video"


@dataclass(frozen=True, slots=True)
class SourceType:
    extension: str
    media_type: str
    kind: SourceKind
    needs_transcription: bool = False


SUPPORTED_SOURCE_TYPES = {
    ".md": SourceType(".md", "text/markdown", SourceKind.document),
    ".docx": SourceType(
        ".docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        SourceKind.document,
    ),
    ".txt": SourceType(".txt", "text/plain", SourceKind.transcript),
    ".vtt": SourceType(".vtt", "text/vtt", SourceKind.transcript),
    ".srt": SourceType(".srt", "application/x-subrip", SourceKind.transcript),
    ".mp3": SourceType(".mp3", "audio/mpeg", SourceKind.audio, True),
    ".wav": SourceType(".wav", "audio/wav", SourceKind.audio, True),
    ".mp4": SourceType(".mp4", "video/mp4", SourceKind.video, True),
    ".mov": SourceType(".mov", "video/quicktime", SourceKind.video, True),
}
