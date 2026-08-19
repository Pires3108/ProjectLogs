import argparse
import json
from pathlib import Path

from app.analysis.models import StructuredAnalysis
from app.config import get_settings
from app.documents.configuration import (
    ContentToggles,
    DocumentConfiguration,
    validate_configuration,
)
from app.documents.html import HtmlGenerator
from app.documents.visual_identity import (
    build_override_style,
    resolve_visual_identity_reference,
)
from app.models import DocumentProfile


def render_analysis(
    analysis_path: str,
    perfil: str,
    toggles_json: str,
    output_path: str,
    mermaid_asset: str | None,
    identidade_visual_documento: str | None = None,
    identidade_visual_diretorio: str | None = None,
) -> None:
    settings = get_settings()
    analysis_data = json.loads(Path(analysis_path).read_text(encoding="utf-8"))
    analysis = StructuredAnalysis.model_validate(analysis_data)
    toggles = ContentToggles.model_validate(json.loads(toggles_json))
    configuration = validate_configuration(
        DocumentConfiguration(perfil=DocumentProfile(perfil), toggles=toggles)
    )
    visual_identity_override = None
    if identidade_visual_documento or identidade_visual_diretorio:
        if not settings.feature_visual_identity:
            print(
                "Aviso: identidade visual de referência ignorada "
                "(defina FEATURE_VISUAL_IDENTITY=true para habilitar este recurso experimental)."
            )
        else:
            identity = resolve_visual_identity_reference(
                document=identidade_visual_documento, directory=identidade_visual_diretorio
            )
            visual_identity_override = build_override_style(identity)
            print(f"Identidade visual aplicada a partir de: {identity.source_path}")
    generator = HtmlGenerator(mermaid_asset_path=mermaid_asset or settings.mermaid_asset_path)
    html = generator.generate(
        analysis, configuration, visual_identity_override=visual_identity_override
    )
    Path(output_path).write_text(html, encoding="utf-8")
    print(f"Documento gerado: {output_path}")
    for warning in configuration.avisos:
        print(f"Aviso: {warning.message}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    render = commands.add_parser(
        "render-analysis",
        help=(
            "Gera o HTML do AtaViva a partir de um JSON de análise já pronto "
            "(sem chamar Gemini/Groq)."
        ),
    )
    render.add_argument(
        "--analysis", required=True, help="Caminho do JSON no formato StructuredAnalysis."
    )
    render.add_argument(
        "--perfil", required=True, choices=[profile.value for profile in DocumentProfile]
    )
    render.add_argument("--toggles", default="{}", help="JSON com os toggles habilitados.")
    render.add_argument("--output", required=True, help="Caminho do arquivo HTML de saída.")
    render.add_argument(
        "--mermaid-asset",
        default=None,
        help="Caminho alternativo para mermaid.min.js (padrão: settings.mermaid_asset_path).",
    )
    identidade_visual = render.add_mutually_exclusive_group()
    identidade_visual.add_argument(
        "--identidade-visual-documento",
        default=None,
        help=(
            "Experimental (requer FEATURE_VISUAL_IDENTITY=true): caminho de um HTML do AtaViva "
            "cuja identidade visual (cores e fontes) deve ser reaplicada neste documento."
        ),
    )
    identidade_visual.add_argument(
        "--identidade-visual-diretorio",
        default=None,
        help=(
            "Experimental (requer FEATURE_VISUAL_IDENTITY=true): diretório com HTMLs do AtaViva; "
            "usa a identidade visual do mais recente."
        ),
    )
    arguments = parser.parse_args()
    if arguments.command == "render-analysis":
        render_analysis(
            arguments.analysis,
            arguments.perfil,
            arguments.toggles,
            arguments.output,
            arguments.mermaid_asset,
            arguments.identidade_visual_documento,
            arguments.identidade_visual_diretorio,
        )


if __name__ == "__main__":
    main()
