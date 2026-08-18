from app.analysis.service import AnalysisService
from app.db.models import JobRecord
from app.documents.configuration import ValidatedConfiguration
from app.documents.html import HtmlGenerator
from app.errors import ApiError
from app.ingestion.normalizers import normalize_source
from app.ingestion.read_ai import parse_read_ai_transcript
from app.ingestion.service import validate_binary_signature
from app.ingestion.storage import SourceStorage
from app.jobs.storage import HtmlStorage
from app.transcription.service import TranscriptionService


class JobProcessor:
    def __init__(
        self,
        *,
        analysis_service: AnalysisService,
        html_generator: HtmlGenerator,
        html_storage: HtmlStorage,
        transcription_service: TranscriptionService | None = None,
        source_storage: SourceStorage | None = None,
        minimum_text_characters: int = 20,
    ) -> None:
        self.analysis_service = analysis_service
        self.html_generator = html_generator
        self.html_storage = html_storage
        self.transcription_service = transcription_service
        self.source_storage = source_storage
        self.minimum_text_characters = minimum_text_characters

    def process(self, job: JobRecord) -> None:
        texts: list[str] = []
        for source in job.sources:
            if source.requires_transcription:
                if self.transcription_service is None:
                    raise ApiError(
                        status_code=503,
                        code="TRANSCRIPTION_NOT_CONFIGURED",
                        message="O serviço de transcrição não está configurado.",
                    )
                if self.source_storage is None:
                    raise ApiError(
                        status_code=503,
                        code="STORAGE_NOT_CONFIGURED",
                        message="O armazenamento de fontes não está configurado.",
                    )
                with self.source_storage.materialize(source.id, source.extension) as path:
                    with path.open("rb") as stream:
                        validate_binary_signature(source.extension, stream.read(12))
                result = self.transcription_service.transcribe(source.id, source.extension)
                source.normalized_text = result.texto
            elif source.normalized_text is None:
                if self.source_storage is None:
                    raise ApiError(
                        status_code=503,
                        code="STORAGE_NOT_CONFIGURED",
                        message="O armazenamento de fontes não está configurado.",
                    )
                with self.source_storage.materialize(source.id, source.extension) as path:
                    content = path.read_bytes()
                validate_binary_signature(source.extension, content)
                if source.extension == ".txt":
                    try:
                        parsed = parse_read_ai_transcript(content)
                    except ApiError:
                        source.normalized_text = normalize_source(source.extension, content)
                    else:
                        source.normalized_text = parsed.texto_normalizado
                        source.format = "read.ai"
                else:
                    source.normalized_text = normalize_source(source.extension, content)
                if len(source.normalized_text) < self.minimum_text_characters:
                    raise ApiError(
                        status_code=422,
                        code="INSUFFICIENT_CONTENT",
                        message="A fonte não contém texto suficiente para análise.",
                    )
            if source.normalized_text:
                texts.append(f"--- FONTE: {source.original_name} ---\n{source.normalized_text}")
        if not texts:
            raise ApiError(
                status_code=422,
                code="INSUFFICIENT_CONTENT",
                message="As fontes não produziram texto suficiente para análise.",
            )
        outcome = self.analysis_service.analyze("\n\n".join(texts))
        avisos = list(job.warnings)
        if outcome.fallback_utilizado:
            avisos.append(
                {
                    "code": "LLM_FALLBACK_PROVIDER_USED",
                    "message": (
                        f"Esta análise foi processada pelo provedor de contingência "
                        f"({outcome.provedor}) porque o provedor principal não respondeu. "
                        "Fontes longas podem ter sido resumidas antes da análise; "
                        "revise decisões, riscos e termos incertos com atenção extra."
                    ),
                }
            )
        configuration = ValidatedConfiguration.model_validate(
            {"perfil": job.perfil, "toggles": job.toggles, "avisos": avisos}
        )
        html = self.html_generator.generate(outcome.analise, configuration)
        job.html_storage_key = self.html_storage.save(job.id, html)
        job.llm_provider = outcome.provedor
        job.analysis_data = outcome.analise.model_dump(mode="json")
