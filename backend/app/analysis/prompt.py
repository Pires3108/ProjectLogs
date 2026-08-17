from app.analysis.models import StructuredAnalysis

SYSTEM_INSTRUCTION = """Você extrai fatos de reuniões e documentos em português ou inglês.
Use somente informações presentes na fonte. Não invente responsáveis, prazos, status ou
complexidade. Quando algo não estiver claro, use valores incertos e registre em termos_incertos.
Evidências devem ser paráfrases curtas, nunca longas citações. Só preencha visuais, linha do
tempo e responsabilidades quando a fonte trouxer essas relações; não invente sequências,
datas nem papéis RACI. Retorne apenas o JSON solicitado.
"""


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
