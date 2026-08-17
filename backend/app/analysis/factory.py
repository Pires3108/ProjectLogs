from app.analysis.gemini import GeminiAnalysisProvider
from app.analysis.groq import GroqAnalysisProvider
from app.analysis.service import AnalysisService
from app.config import Settings
from app.errors import ApiError


def create_analysis_service(settings: Settings) -> AnalysisService:
    if settings.gemini_api_key is None or settings.groq_api_key is None:
        raise ApiError(
            status_code=503,
            code="LLM_NOT_CONFIGURED",
            message="Os provedores de análise não estão configurados.",
        )
    return AnalysisService(
        primary=GeminiAnalysisProvider(
            api_key=settings.gemini_api_key.get_secret_value(),
            model=settings.gemini_analysis_model,
            base_url=settings.gemini_api_base_url,
        ),
        fallback=GroqAnalysisProvider(
            api_key=settings.groq_api_key.get_secret_value(),
            model=settings.groq_analysis_model,
            url=settings.groq_chat_url,
            max_input_characters=settings.groq_analysis_max_input_characters,
        ),
        max_attempts=settings.llm_max_attempts,
        backoff_seconds=settings.llm_backoff_seconds,
    )
