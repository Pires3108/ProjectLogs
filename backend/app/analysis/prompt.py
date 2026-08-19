from enum import StrEnum

from app.analysis.models import StructuredAnalysis

SYSTEM_INSTRUCTION = """Você extrai fatos de reuniões e documentos em português ou inglês.
Use somente informações presentes na fonte. Não invente responsáveis, prazos, status ou
complexidade. Quando algo não estiver claro, use valores incertos e registre em termos_incertos.
Evidências devem ser paráfrases curtas, nunca longas citações. Só preencha visuais, linha do
tempo e responsabilidades quando a fonte trouxer essas relações; não invente sequências,
datas nem papéis RACI. Retorne apenas o JSON solicitado.
"""


class DepthLevel(StrEnum):
    raso = "raso"
    medio = "medio"
    profundo = "profundo"
    estendido = "estendido"


DEPTH_LEVEL_LABELS: dict[DepthLevel, str] = {
    DepthLevel.raso: "Raso",
    DepthLevel.medio: "Médio",
    DepthLevel.profundo: "Profundo",
    DepthLevel.estendido: "Estendido",
}

# Cada nível descreve o quanto a extração deve se aprofundar na fonte. Isto não
# altera o schema (StructuredAnalysis continua igual) nem os limites de
# objetivo/resumo acima — afeta apenas quantos itens/evidências/exemplos/termos
# são extraídos e o quão detalhada é cada descrição. Nível mais profundo =
# mais tokens de leitura e de saída, e um documento final mais longo.
DEPTH_LEVEL_INSTRUCTIONS: dict[DepthLevel, str] = {
    DepthLevel.raso: (
        "Nível de profundidade: RASO. Extraia só o essencial: os itens de trabalho, "
        "decisões e riscos mais importantes (ignore menções secundárias ou tangenciais). "
        "Descrições de itens em 1 frase objetiva. No máximo 1 evidência por item, sem "
        "exemplos a menos que sejam centrais. Glossário só com os termos indispensáveis "
        "para entender o objetivo. Linha do tempo e responsabilidades só se muito "
        "evidentes na fonte."
    ),
    DepthLevel.medio: (
        "Nível de profundidade: MÉDIO. Cobertura equilibrada: inclua todos os itens de "
        "trabalho, decisões e riscos claramente discutidos, com descrições de 1 a 2 "
        "frases e 1 a 2 evidências por item quando disponíveis. Inclua exemplos quando "
        "ajudarem a esclarecer um item. Glossário com os termos técnicos relevantes."
    ),
    DepthLevel.profundo: (
        "Nível de profundidade: PROFUNDO. Extraia de forma abrangente: todos os itens de "
        "trabalho, decisões, riscos e termos incertos mencionados, mesmo os secundários. "
        "Descrições mais completas (2 a 3 frases) e múltiplas evidências por item quando a "
        "fonte permitir. Inclua exemplos sempre que a fonte trouxer algum. Glossário "
        "abrangente e linha do tempo/responsabilidades detalhadas sempre que a fonte tiver "
        "elementos para isso."
    ),
    DepthLevel.estendido: (
        "Nível de profundidade: ESTENDIDO. Extração exaustiva: não descarte nenhum item, "
        "decisão, risco ou termo incerto presente na fonte, incluindo detalhes menores. "
        "Descrições completas e todas as evidências/exemplos disponíveis por item. "
        "Glossário o mais completo possível e linha do tempo/responsabilidades com o "
        "maior nível de granularidade que a fonte suportar. Isto consome mais tokens de "
        "leitura e de saída e produz o documento mais longo — use somente quando o "
        "usuário pedir profundidade máxima."
    ),
}

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


def build_analysis_prompt(text: str, depth: DepthLevel = DepthLevel.medio) -> str:
    return (
        "Analise a fonte delimitada abaixo. Extraia objetivo, resumo, itens de trabalho, "
        "decisões, riscos e termos incertos. O campo objetivo é um título: uma frase curta "
        "e direta (até ~60 caracteres), nunca uma frase longa ou composta por várias ideias. "
        "O campo resumo é curto (1 a 3 frases, até ~280 caracteres) — não liste detalhes "
        "nele; cada detalhe específico vai no campo apropriado (itens, decisoes, riscos, "
        "termos_incertos etc). Para complexidade, use 'incerta' quando a fonte não trouxer "
        f"elementos suficientes.\n\n{DEPTH_LEVEL_INSTRUCTIONS[depth]}\n\n<FONTE>\n"
        f"{text}\n"
        "</FONTE>"
    )


def analysis_json_schema() -> dict:
    return StructuredAnalysis.model_json_schema()
