from datetime import datetime

from pydantic import BaseModel

from app.db.models import JobStatus
from app.documents.configuration import ConfigurationWarning, ContentToggles
from app.ingestion.types import SourceKind
from app.models import DocumentProfile


class JobSourceResponse(BaseModel):
    id: str
    nome: str
    formato: str
    tipo: SourceKind
    tamanho_bytes: int
    requer_transcricao: bool


class JobResponse(BaseModel):
    id: str
    status: JobStatus
    perfil: DocumentProfile
    toggles: ContentToggles
    avisos: list[ConfigurationWarning]
    fontes: list[JobSourceResponse]
    provedor_llm: str | None
    analise: dict | None
    erro: dict | None
    html_url: str | None
    criado_em: datetime
    atualizado_em: datetime
    fila_posicao: int | None
    fila_estimativa_minutos: int | None


class DirectJobRequest(BaseModel):
    perfil: DocumentProfile
    toggles: ContentToggles
    tickets: list[str]
