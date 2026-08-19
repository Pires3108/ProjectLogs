from enum import StrEnum


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
