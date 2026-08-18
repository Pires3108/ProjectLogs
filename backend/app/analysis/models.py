from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WorkStatus(StrEnum):
    concluido = "concluido"
    em_andamento = "em_andamento"
    pendente = "pendente"
    bloqueado = "bloqueado"
    incerto = "incerto"


class Complexity(StrEnum):
    baixa = "baixa"
    media = "media"
    alta = "alta"
    incerta = "incerta"


class VisualType(StrEnum):
    fluxograma = "fluxograma"
    diagrama = "diagrama"


class VisualNode(StrictModel):
    id: str = Field(min_length=1)
    rotulo: str = Field(min_length=1)


class VisualConnection(StrictModel):
    origem: str = Field(min_length=1)
    destino: str = Field(min_length=1)
    rotulo: str | None


class VisualDefinition(StrictModel):
    titulo: str = Field(min_length=1)
    tipo: VisualType
    nos: list[VisualNode]
    conexoes: list[VisualConnection]


class GlossaryTerm(StrictModel):
    termo: str = Field(min_length=1)
    definicao: str = Field(min_length=1)


class TimelineEvent(StrictModel):
    titulo: str = Field(min_length=1)
    quando: str | None
    descricao: str = Field(min_length=1)


class ResponsibilityEntry(StrictModel):
    atividade: str = Field(min_length=1)
    responsavel: str | None
    aprovador: str | None
    consultados: list[str]
    informados: list[str]


class WorkItem(StrictModel):
    titulo: str = Field(min_length=1)
    descricao: str = Field(min_length=1)
    status: WorkStatus
    responsavel: str | None
    complexidade: Complexity
    evidencias: list[str]
    exemplos: list[str]


class StructuredAnalysis(StrictModel):
    objetivo: str = Field(
        min_length=1,
        description=(
            "Título curto e direto, como manchete (ideal até ~60 caracteres, "
            "nunca uma frase longa ou composta)."
        ),
    )
    resumo: str = Field(min_length=1)
    itens: list[WorkItem]
    decisoes: list[str]
    riscos: list[str]
    termos_incertos: list[str]
    visuais: list[VisualDefinition]
    glossario: list[GlossaryTerm]
    linha_do_tempo: list[TimelineEvent]
    responsabilidades: list[ResponsibilityEntry]


class AnalysisOutcome(StrictModel):
    analise: StructuredAnalysis
    provedor: str
    modelo: str
    fallback_utilizado: bool
