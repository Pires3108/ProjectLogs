import json
from pathlib import Path

from app.cli import render_analysis
from tests.analysis_fixtures import VALID_ANALYSIS


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
