from pydantic import BaseModel, ConfigDict

from app.models import ContentToggle, DocumentProfile


class ContentToggles(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fluxogramas: bool = False
    diagramas: bool = False
    exemplos: bool = False
    exercicios: bool = False
    glossario: bool = False
    linha_do_tempo: bool = False
    matriz_responsabilidade: bool = False


class DocumentConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    perfil: DocumentProfile
    toggles: ContentToggles


class ConfigurationWarning(BaseModel):
    code: str
    message: str
    toggle: ContentToggle | None = None


class ValidatedConfiguration(BaseModel):
    perfil: DocumentProfile
    toggles: ContentToggles
    avisos: list[ConfigurationWarning]


class ProfileRules(BaseModel):
    nome: str
    foco: str
    tom: str
    secoes_obrigatorias: list[str]
    toggles_permitidos: frozenset[ContentToggle]


COMMON_TOGGLES = frozenset(
    {ContentToggle.fluxogramas, ContentToggle.diagramas, ContentToggle.exemplos}
)

PROFILE_RULES: dict[DocumentProfile, ProfileRules] = {
    DocumentProfile.estudo: ProfileRules(
        nome="Estudo",
        foco="Explicar o conteúdo para aprendizado.",
        tom="Didático, claro e progressivo.",
        secoes_obrigatorias=["Resumo do tema", "Conceitos-chave", "Aprofundamento"],
        toggles_permitidos=COMMON_TOGGLES | {ContentToggle.exercicios, ContentToggle.glossario},
    ),
    DocumentProfile.organizacao: ProfileRules(
        nome="Organização",
        foco="Estruturar decisões, ações, prazos e responsabilidades.",
        tom="Objetivo, operacional e rastreável.",
        secoes_obrigatorias=["Decisões", "Ações e prazos"],
        toggles_permitidos=COMMON_TOGGLES
        | {ContentToggle.linha_do_tempo, ContentToggle.matriz_responsabilidade},
    ),
    DocumentProfile.backlog: ProfileRules(
        nome="Backlog do projeto",
        foco="Rastrear o que foi feito e o que falta executar.",
        tom="Técnico, priorizável e orientado à execução.",
        secoes_obrigatorias=["Concluído", "Pendente", "Bloqueios"],
        toggles_permitidos=COMMON_TOGGLES | {ContentToggle.matriz_responsabilidade},
    ),
}


def validate_configuration(configuration: DocumentConfiguration) -> ValidatedConfiguration:
    allowed = PROFILE_RULES[configuration.perfil].toggles_permitidos
    effective = configuration.toggles.model_dump()
    warnings: list[ConfigurationWarning] = []
    for toggle in ContentToggle:
        if effective[toggle.value] and toggle not in allowed:
            effective[toggle.value] = False
            warnings.append(
                ConfigurationWarning(
                    code="TOGGLE_IGNORED_FOR_PROFILE",
                    message=(
                        f"O toggle '{toggle.value}' foi desativado porque não se aplica "
                        f"ao perfil '{configuration.perfil.value}'."
                    ),
                    toggle=toggle,
                )
            )
    return ValidatedConfiguration(
        perfil=configuration.perfil,
        toggles=ContentToggles.model_validate(effective),
        avisos=warnings,
    )
