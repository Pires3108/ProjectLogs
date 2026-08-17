from app.analysis.models import StructuredAnalysis

SYSTEM_INSTRUCTION = """Você extrai fatos de reuniões e documentos em português ou inglês.
Use somente informações presentes na fonte. Não invente responsáveis, prazos, status ou
complexidade. Quando algo não estiver claro, use valores incertos e registre em termos_incertos.
Evidências devem ser paráfrases curtas, nunca longas citações. Só preencha visuais, linha do
tempo e responsabilidades quando a fonte trouxer essas relações; não invente sequências,
datas nem papéis RACI. Retorne apenas o JSON solicitado.
"""

OMISSION_MARKER = "\n\n[...trecho omitido para respeitar o limite do provedor...]\n\n"


def distributed_excerpt(text: str, max_characters: int) -> str:
    """Preserva início, centro e fim quando um provedor exige uma entrada menor."""
    if max_characters <= 0 or len(text) <= max_characters:
        return text
    available = max_characters - 2 * len(OMISSION_MARKER)
    if available < 3:
        return text[:max_characters]
    segment = available // 3
    middle_start = max(0, len(text) // 2 - segment // 2)
    end_size = available - 2 * segment
    return (
        text[:segment]
        + OMISSION_MARKER
        + text[middle_start : middle_start + segment]
        + OMISSION_MARKER
        + text[-end_size:]
    )


def build_analysis_prompt(text: str) -> str:
    return (
        "Analise a fonte delimitada abaixo. Extraia objetivo, resumo, itens de trabalho, "
        "decisões, riscos e termos incertos. Para complexidade, use 'incerta' quando a fonte "
        "não trouxer elementos suficientes.\n\n<FONTE>\n"
        f"{text}\n"
        "</FONTE>"
    )


def analysis_json_schema() -> dict:
    return StructuredAnalysis.model_json_schema()
