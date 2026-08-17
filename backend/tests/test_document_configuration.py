import pytest

from app.documents.configuration import (
    ContentToggles,
    DocumentConfiguration,
    validate_configuration,
)
from app.models import DocumentProfile


@pytest.mark.parametrize("profile", list(DocumentProfile))
def test_common_toggles_are_allowed_for_every_profile(profile: DocumentProfile) -> None:
    result = validate_configuration(
        DocumentConfiguration(
            perfil=profile,
            toggles=ContentToggles(fluxogramas=True, diagramas=True, exemplos=True),
        )
    )

    assert result.toggles.fluxogramas is True
    assert result.toggles.diagramas is True
    assert result.toggles.exemplos is True
    assert result.avisos == []


def test_exercises_are_ignored_outside_study_with_warning() -> None:
    result = validate_configuration(
        DocumentConfiguration(
            perfil=DocumentProfile.backlog,
            toggles=ContentToggles(exercicios=True),
        )
    )

    assert result.toggles.exercicios is False
    assert result.avisos[0].code == "TOGGLE_IGNORED_FOR_PROFILE"
    assert result.avisos[0].toggle == "exercicios"


def test_timeline_is_allowed_for_organization() -> None:
    result = validate_configuration(
        DocumentConfiguration(
            perfil=DocumentProfile.organizacao,
            toggles=ContentToggles(linha_do_tempo=True),
        )
    )

    assert result.toggles.linha_do_tempo is True
    assert result.avisos == []
