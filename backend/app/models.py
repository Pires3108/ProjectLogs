from enum import StrEnum

from pydantic import BaseModel

from app.ingestion.types import SourceKind


class DocumentProfile(StrEnum):
    estudo = "estudo"
    organizacao = "organizacao"
    backlog = "backlog"


class ContentToggle(StrEnum):
    fluxogramas = "fluxogramas"
    diagramas = "diagramas"
    exemplos = "exemplos"
    exercicios = "exercicios"
    glossario = "glossario"
    linha_do_tempo = "linha_do_tempo"
    matriz_responsabilidade = "matriz_responsabilidade"


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ProfileDefinition(BaseModel):
    perfil: DocumentProfile
    toggles_permitidos: list[ContentToggle]
    secoes_obrigatorias: list[str]
    foco: str


class CapabilitiesResponse(BaseModel):
    perfis: list[ProfileDefinition]
    formatos_planejados_v1: list[str]


class IngestedSource(BaseModel):
    id: str
    nome: str
    formato: str
    tipo: SourceKind
    tamanho_bytes: int
    requer_transcricao: bool
    texto_normalizado: str | None = None


class IngestionResponse(BaseModel):
    fontes: list[IngestedSource]
    total_fontes: int
    pronto_para_analise: bool
