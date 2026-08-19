import json
from pathlib import Path

from app.cli import render_analysis
from app.config import get_settings
from tests.analysis_fixtures import VALID_ANALYSIS

_REFERENCE_HTML = "<style>:root { --accent:#123456; --spark:#654321; }</style>"


def test_render_analysis_generates_html_without_calling_any_llm_provider(tmp_path: Path) -> None:
    analysis_path = tmp_path / "analysis.json"
    analysis_path.write_text(json.dumps(VALID_ANALYSIS, ensure_ascii=False), encoding="utf-8")
    output_path = tmp_path / "documento.html"

    render_analysis(
        str(analysis_path),
        "backlog",
        "{}",
        str(output_path),
        str(tmp_path / "missing-mermaid.js"),
    )

    html = output_path.read_text(encoding="utf-8")
    assert "<!doctype html>" in html
    assert "Backlog do projeto" in html
    assert VALID_ANALYSIS["objetivo"] in html


def test_render_analysis_reports_toggle_warnings_ignored_for_profile(
    tmp_path: Path, capsys
) -> None:
    analysis_path = tmp_path / "analysis.json"
    analysis_path.write_text(json.dumps(VALID_ANALYSIS, ensure_ascii=False), encoding="utf-8")
    output_path = tmp_path / "documento.html"

    render_analysis(
        str(analysis_path),
        "backlog",
        json.dumps({"exercicios": True}),
        str(output_path),
        str(tmp_path / "missing-mermaid.js"),
    )

    assert "Aviso:" in capsys.readouterr().out


def test_render_analysis_ignores_visual_identity_reference_when_flag_disabled(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("FEATURE_VISUAL_IDENTITY", "false")
    get_settings.cache_clear()
    analysis_path = tmp_path / "analysis.json"
    analysis_path.write_text(json.dumps(VALID_ANALYSIS, ensure_ascii=False), encoding="utf-8")
    reference_path = tmp_path / "referencia.html"
    reference_path.write_text(_REFERENCE_HTML, encoding="utf-8")
    output_path = tmp_path / "documento.html"

    render_analysis(
        str(analysis_path),
        "backlog",
        "{}",
        str(output_path),
        str(tmp_path / "missing-mermaid.js"),
        str(reference_path),
        None,
    )

    assert "FEATURE_VISUAL_IDENTITY" in capsys.readouterr().out
    assert "--accent:#123456" not in output_path.read_text(encoding="utf-8")
    get_settings.cache_clear()


def test_render_analysis_applies_visual_identity_reference_when_flag_enabled(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("FEATURE_VISUAL_IDENTITY", "true")
    get_settings.cache_clear()
    analysis_path = tmp_path / "analysis.json"
    analysis_path.write_text(json.dumps(VALID_ANALYSIS, ensure_ascii=False), encoding="utf-8")
    reference_path = tmp_path / "referencia.html"
    reference_path.write_text(_REFERENCE_HTML, encoding="utf-8")
    output_path = tmp_path / "documento.html"

    render_analysis(
        str(analysis_path),
        "backlog",
        "{}",
        str(output_path),
        str(tmp_path / "missing-mermaid.js"),
        str(reference_path),
        None,
    )

    output = output_path.read_text(encoding="utf-8")
    assert "Identidade visual aplicada" in capsys.readouterr().out
    assert "--accent:#123456;--spark:#654321;" in output
    get_settings.cache_clear()
