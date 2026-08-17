from datetime import date

import pytest

from app.errors import ApiError
from app.ingestion.read_ai import parse_read_ai_transcript

SYNTHETIC_EXPORT = """Reunião de planejamento
seg., 17 de ago. de 2026

0:00 - Ana Exemplo - Equipe A
Bom dia. Vamos revisar a entrega.

1:05 - Palestrante Não Identificado
A primeira etapa foi concluída.
O teste será executado amanhã.

12:34 - Bruno Exemplo
Ficarei responsável pela documentação.
"""


def test_parses_read_ai_text_export() -> None:
    transcript = parse_read_ai_transcript(SYNTHETIC_EXPORT.encode())

    assert transcript.titulo == "Reunião de planejamento"
    assert transcript.data_reuniao == date(2026, 8, 17)
    assert len(transcript.falas) == 3
    assert transcript.falas[1].inicio_segundos == 65
    assert transcript.falas[1].locutor == "Palestrante Não Identificado"
    assert "teste será executado" in transcript.falas[1].texto
    assert "Ana Exemplo - Equipe A: Bom dia" in transcript.texto_normalizado


def test_rejects_plain_text_as_read_ai_export() -> None:
    with pytest.raises(ApiError) as captured:
        parse_read_ai_transcript(b"Um texto comum sem marcadores de fala suficientes.")

    assert captured.value.code == "INVALID_READ_AI_EXPORT"
