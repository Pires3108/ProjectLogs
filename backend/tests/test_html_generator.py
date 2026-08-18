from copy import deepcopy
from pathlib import Path

import pytest

from app.analysis.models import StructuredAnalysis
from app.documents.configuration import (
    ContentToggles,
    DocumentConfiguration,
    validate_configuration,
)
from app.documents.html import HtmlGenerator
from app.models import DocumentProfile
from tests.analysis_fixtures import VALID_ANALYSIS


@pytest.mark.parametrize(
    ("profile", "expected_heading"),
    [
        (DocumentProfile.estudo, "Conceitos-chave"),
        (DocumentProfile.organizacao, "Decisões tomadas"),
        (DocumentProfile.backlog, "Pendente"),
    ],
)
def test_generates_responsive_profile_html_without_external_assets(
    tmp_path: Path, profile: DocumentProfile, expected_heading: str
) -> None:
    configuration = validate_configuration(
        DocumentConfiguration(perfil=profile, toggles=ContentToggles())
    )
    generator = HtmlGenerator(mermaid_asset_path=str(tmp_path / "missing.js"))

    html = generator.generate(StructuredAnalysis.model_validate(VALID_ANALYSIS), configuration)

    assert "<!doctype html>" in html
    assert expected_heading in html
    assert 'class="hero-aside"' in html
    assert 'class="nav-wrap"' in html
    assert 'id="readingMeter"' in html
    assert "@media print" in html
    assert "https://" not in html
    assert "mermaid.initialize" not in html


def test_renders_only_enabled_nonempty_sections(tmp_path: Path) -> None:
    data = deepcopy(VALID_ANALYSIS)
    data["glossario"] = [{"termo": "API", "definicao": "Interface entre sistemas."}]
    analysis = StructuredAnalysis.model_validate(data)
    generator = HtmlGenerator(mermaid_asset_path=str(tmp_path / "missing.js"))

    disabled = generator.generate(
        analysis,
        validate_configuration(
            DocumentConfiguration(perfil="estudo", toggles=ContentToggles(glossario=False))
        ),
    )
    enabled = generator.generate(
        analysis,
        validate_configuration(
            DocumentConfiguration(perfil="estudo", toggles=ContentToggles(glossario=True))
        ),
    )

    assert "<h2>Glossário</h2>" not in disabled
    assert "<h2>Glossário</h2>" in enabled
    assert "Interface entre sistemas." in enabled


def test_embeds_mermaid_offline_and_sanitizes_diagram_labels(tmp_path: Path) -> None:
    asset = tmp_path / "mermaid.min.js"
    asset.write_text("const mermaid={initialize:()=>{}};", encoding="utf-8")
    data = deepcopy(VALID_ANALYSIS)
    data["visuais"] = [
        {
            "titulo": "Fluxo explícito",
            "tipo": "fluxograma",
            "nos": [
                {"id": "raw-a", "rotulo": "Entrada<script>"},
                {"id": "raw-b", "rotulo": "Saída"},
            ],
            "conexoes": [{"origem": "raw-a", "destino": "raw-b", "rotulo": "válido"}],
        }
    ]
    generator = HtmlGenerator(mermaid_asset_path=str(asset))
    configuration = validate_configuration(
        DocumentConfiguration(perfil="organizacao", toggles=ContentToggles(fluxogramas=True))
    )

    html = generator.generate(StructuredAnalysis.model_validate(data), configuration)

    assert "const mermaid=" in html
    assert "mermaid.initialize" in html
    assert "flowchart TD" in html
    assert "Entrada&lt;script&gt;" not in html
    assert "Entradascript" in html


def test_escapes_untrusted_analysis_text(tmp_path: Path) -> None:
    data = deepcopy(VALID_ANALYSIS)
    data["objetivo"] = "<script>alert('x')</script>"
    generator = HtmlGenerator(mermaid_asset_path=str(tmp_path / "missing.js"))
    configuration = validate_configuration(
        DocumentConfiguration(perfil="backlog", toggles=ContentToggles())
    )

    html = generator.generate(StructuredAnalysis.model_validate(data), configuration)

    assert "&lt;script&gt;alert" in html
    assert "<script>alert('x')</script>" not in html
