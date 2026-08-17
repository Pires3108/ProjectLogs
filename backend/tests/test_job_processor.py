from pathlib import Path

from app.analysis.models import AnalysisOutcome, StructuredAnalysis
from app.db.models import JobRecord, SourceRecord
from app.documents.html import HtmlGenerator
from app.jobs.processor import JobProcessor
from app.jobs.storage import LocalHtmlStorage
from tests.analysis_fixtures import VALID_ANALYSIS


class StubAnalysisService:
    def analyze(self, text: str) -> AnalysisOutcome:
        assert "conteúdo sintético" in text
        return AnalysisOutcome(
            analise=StructuredAnalysis.model_validate(VALID_ANALYSIS),
            provedor="stub",
            modelo="stub-v1",
            fallback_utilizado=False,
        )


def test_processes_text_job_into_self_contained_html(tmp_path: Path) -> None:
    job = JobRecord(
        id="00000000-0000-0000-0000-000000000001",
        api_key_id="00000000-0000-0000-0000-000000000002",
        perfil="backlog",
        toggles={
            "fluxogramas": False,
            "diagramas": False,
            "exemplos": False,
            "exercicios": False,
            "glossario": False,
            "linha_do_tempo": False,
            "matriz_responsabilidade": False,
        },
        warnings=[],
    )
    job.sources = [
        SourceRecord(
            id="00000000-0000-0000-0000-000000000003",
            job_id=job.id,
            original_name="fonte.txt",
            extension=".txt",
            format="txt",
            kind="transcript",
            size_bytes=40,
            requires_transcription=False,
            normalized_text="Este é um conteúdo sintético para o teste.",
        )
    ]
    processor = JobProcessor(
        analysis_service=StubAnalysisService(),  # type: ignore[arg-type]
        html_generator=HtmlGenerator(mermaid_asset_path=str(tmp_path / "missing.js")),
        html_storage=LocalHtmlStorage(str(tmp_path / "html")),
    )

    processor.process(job)

    assert job.llm_provider == "stub"
    assert job.analysis_data["objetivo"] == VALID_ANALYSIS["objetivo"]
    assert job.html_storage_key == f"{job.id}.html"
    generated = (tmp_path / "html" / job.html_storage_key).read_text(encoding="utf-8")
    assert "Backlog do projeto" in generated
    assert "https://" not in generated
