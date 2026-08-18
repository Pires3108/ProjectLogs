import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.analysis.models import StructuredAnalysis
from app.auth.keys import issue_api_key
from app.config import get_settings
from app.db.models import JobRecord
from app.db.session import get_session_factory
from app.documents.configuration import (
    ContentToggles,
    DocumentConfiguration,
    validate_configuration,
)
from app.documents.html import HtmlGenerator
from app.ingestion.storage import create_source_storage
from app.jobs.storage import create_html_storage
from app.models import DocumentProfile


def create_api_key(name: str, expires_in_days: int | None) -> None:
    settings = get_settings()
    expires_at = (
        datetime.now(UTC) + timedelta(days=expires_in_days) if expires_in_days is not None else None
    )
    raw_key, record = issue_api_key(
        name,
        settings.api_key_pepper.get_secret_value(),
        expires_at=expires_at,
    )
    with get_session_factory()() as session:
        session.add(record)
        session.commit()
    print("API Key criada. Copie agora; ela não poderá ser recuperada novamente:")
    print(raw_key)


def cleanup_jobs(before: datetime, execute: bool) -> None:
    if before.tzinfo is None:
        raise SystemExit("--before deve incluir fuso horário, por exemplo 2026-09-01T00:00:00Z")
    settings = get_settings()
    source_storage = create_source_storage(settings)
    html_storage = create_html_storage(settings)
    with get_session_factory()() as session:
        jobs = session.scalars(
            select(JobRecord)
            .options(selectinload(JobRecord.sources))
            .where(JobRecord.status.in_(["done", "failed"]), JobRecord.updated_at < before)
        ).all()
        print(f"Jobs elegíveis: {len(jobs)}")
        if not execute:
            print("Simulação apenas; use --execute para remover definitivamente.")
            return
        for job in jobs:
            for source in job.sources:
                source_storage.delete(source.id, source.extension)
            if job.html_storage_key:
                html_storage.delete(job.html_storage_key)
            session.delete(job)
        session.commit()
        print(f"Jobs removidos: {len(jobs)}")


def render_analysis(
    analysis_path: str,
    perfil: str,
    toggles_json: str,
    output_path: str,
    mermaid_asset: str | None,
) -> None:
    settings = get_settings()
    analysis_data = json.loads(Path(analysis_path).read_text(encoding="utf-8"))
    analysis = StructuredAnalysis.model_validate(analysis_data)
    toggles = ContentToggles.model_validate(json.loads(toggles_json))
    configuration = validate_configuration(
        DocumentConfiguration(perfil=DocumentProfile(perfil), toggles=toggles)
    )
    generator = HtmlGenerator(mermaid_asset_path=mermaid_asset or settings.mermaid_asset_path)
    html = generator.generate(analysis, configuration)
    Path(output_path).write_text(html, encoding="utf-8")
    print(f"Documento gerado: {output_path}")
    for warning in configuration.avisos:
        print(f"Aviso: {warning.message}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-api-key")
    create.add_argument("--name", required=True)
    create.add_argument("--expires-in-days", type=int)
    cleanup = commands.add_parser("cleanup-jobs")
    cleanup.add_argument("--before", type=datetime.fromisoformat, required=True)
    cleanup.add_argument("--execute", action="store_true")
    render = commands.add_parser(
        "render-analysis",
        help="Gera o HTML do AtaViva a partir de um JSON de análise já pronto (sem chamar Gemini/Groq).",
    )
    render.add_argument("--analysis", required=True, help="Caminho do JSON no formato StructuredAnalysis.")
    render.add_argument("--perfil", required=True, choices=[profile.value for profile in DocumentProfile])
    render.add_argument("--toggles", default="{}", help="JSON com os toggles habilitados.")
    render.add_argument("--output", required=True, help="Caminho do arquivo HTML de saída.")
    render.add_argument(
        "--mermaid-asset",
        default=None,
        help="Caminho alternativo para mermaid.min.js (padrão: settings.mermaid_asset_path).",
    )
    arguments = parser.parse_args()
    if arguments.command == "create-api-key":
        create_api_key(arguments.name, arguments.expires_in_days)
    elif arguments.command == "cleanup-jobs":
        cleanup_jobs(arguments.before, arguments.execute)
    elif arguments.command == "render-analysis":
        render_analysis(
            arguments.analysis,
            arguments.perfil,
            arguments.toggles,
            arguments.output,
            arguments.mermaid_asset,
        )


if __name__ == "__main__":
    main()
