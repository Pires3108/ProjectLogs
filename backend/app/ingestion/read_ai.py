import re
from datetime import date

from pydantic import BaseModel, Field

from app.errors import ApiError
from app.ingestion.normalizers import decode_text

UTTERANCE_HEADER = re.compile(r"^(?P<minutes>\d+):(?P<seconds>[0-5]\d)\s+-\s+(?P<speaker>.+?)\s*$")
DATE_PATTERN = re.compile(
    r"(?P<day>\d{1,2})\s+de\s+(?P<month>[a-zç]+)\.?\s+de\s+(?P<year>\d{4})",
    re.I,
)
MONTHS = {
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


class ReadAIUtterance(BaseModel):
    inicio_segundos: int = Field(ge=0)
    locutor: str = Field(min_length=1)
    texto: str = Field(min_length=1)


class ReadAITranscript(BaseModel):
    titulo: str
    data_reuniao: date | None = None
    falas: list[ReadAIUtterance]

    @property
    def texto_normalizado(self) -> str:
        return "\n".join(f"{item.locutor}: {item.texto}" for item in self.falas)


def parse_read_ai_transcript(content: bytes) -> ReadAITranscript:
    lines = decode_text(content).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    non_empty = [(index, line.strip()) for index, line in enumerate(lines) if line.strip()]
    if not non_empty:
        raise _invalid_export()
    title = non_empty[0][1]
    meeting_date = _parse_date(non_empty[1][1]) if len(non_empty) > 1 else None
    utterances: list[ReadAIUtterance] = []
    current_header: re.Match[str] | None = None
    current_text: list[str] = []

    def flush() -> None:
        nonlocal current_header, current_text
        text = " ".join(current_text).strip()
        if current_header is not None and text:
            utterances.append(
                ReadAIUtterance(
                    inicio_segundos=int(current_header["minutes"]) * 60
                    + int(current_header["seconds"]),
                    locutor=current_header["speaker"].strip(),
                    texto=text,
                )
            )
        current_text = []

    for _, line in non_empty[1:]:
        header = UTTERANCE_HEADER.fullmatch(line)
        if header:
            flush()
            current_header = header
        elif current_header is not None:
            current_text.append(line)
    flush()
    if not utterances:
        raise _invalid_export()
    return ReadAITranscript(titulo=title, data_reuniao=meeting_date, falas=utterances)


def _parse_date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    if not match:
        return None
    month = MONTHS.get(match["month"].lower().rstrip("."))
    if month is None:
        return None
    return date(int(match["year"]), month, int(match["day"]))


def _invalid_export() -> ApiError:
    return ApiError(
        status_code=400,
        code="INVALID_READ_AI_EXPORT",
        message="O arquivo não corresponde ao formato de transcrição exportado pelo Read.AI.",
    )
