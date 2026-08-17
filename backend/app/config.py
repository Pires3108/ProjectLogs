from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AtaViva API"
    app_version: str = "0.1.0"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"
    max_document_bytes: int = 20 * 1024 * 1024
    max_audio_bytes: int = 200 * 1024 * 1024
    max_video_bytes: int = 500 * 1024 * 1024
    minimum_text_characters: int = 20
    upload_root: str = "runtime/uploads"
    groq_api_key: SecretStr | None = None
    groq_transcription_model: str = "whisper-large-v3-turbo"
    groq_transcription_url: str = "https://api.groq.com/openai/v1/audio/transcriptions"
    transcription_chunk_seconds: int = 1200
    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"
    max_media_duration_seconds: int = 3 * 60 * 60
    gemini_api_key: SecretStr | None = None
    gemini_analysis_model: str = "gemini-3.6-flash"
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    groq_analysis_model: str = "openai/gpt-oss-120b"
    groq_chat_url: str = "https://api.groq.com/openai/v1/chat/completions"
    llm_max_attempts: int = 3
    llm_backoff_seconds: float = 2.0
    groq_analysis_max_input_characters: int = 16_000
    mermaid_asset_path: str = "app/static/vendor/mermaid.min.js"
    database_url: str = "sqlite:///runtime/ataviva.db"
    database_url_unpooled: str | None = None
    api_key_pepper: SecretStr = SecretStr("development-only-change-me")
    generated_html_root: str = "runtime/generated-html"
    html_storage_backend: str = "local"
    redis_url: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = False
    api_rate_limit_per_minute: int = 60
    quota_warning_ratio: float = 0.1
    job_dispatcher: str = "celery"
    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"
    google_cloud_tasks_queue: str = "ataviva-jobs"
    cloud_tasks_worker_url: str | None = None
    cloud_tasks_service_account_email: str | None = None
    internal_task_secret: SecretStr = SecretStr("development-internal-task-secret")
    storage_backend: str = "local"
    storage_endpoint: str | None = None
    storage_access_key: SecretStr | None = None
    storage_secret_key: SecretStr | None = None
    storage_bucket: str = "ataviva"
    storage_region: str = "auto"
    direct_upload_expiry_seconds: int = 900
    estimated_job_minutes: int = 5

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    @field_validator("database_url", "database_url_unpooled", mode="before")
    @classmethod
    def use_psycopg_driver(cls, value: str | None) -> str | None:
        if value and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @field_validator("gemini_analysis_model", mode="before")
    @classmethod
    def replace_retired_gemini_model(cls, value: str) -> str:
        if value == "gemini-2.5-flash":
            return "gemini-3.6-flash"
        return value

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
