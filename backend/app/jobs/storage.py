from pathlib import Path
from typing import Protocol

from botocore.exceptions import BotoCoreError, ClientError

from app.config import Settings
from app.db.models import JobRecord
from app.db.session import get_session_factory
from app.errors import ApiError
from app.ingestion.storage import create_s3_client


class HtmlStorage(Protocol):
    def save(self, job_id: str, html: str) -> str: ...

    def load(self, storage_key: str) -> bytes: ...

    def delete(self, storage_key: str) -> None: ...


class LocalHtmlStorage:
    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()

    def _resolve(self, storage_key: str) -> Path:
        destination = (self.root / storage_key).resolve()
        if self.root not in destination.parents:
            raise ApiError(
                status_code=400,
                code="INVALID_STORAGE_KEY",
                message="A referência do HTML é inválida.",
            )
        return destination

    def save(self, job_id: str, html: str) -> str:
        self.root.mkdir(parents=True, exist_ok=True)
        storage_key = f"{job_id}.html"
        destination = self._resolve(storage_key)
        temporary = destination.with_suffix(".tmp")
        temporary.write_text(html, encoding="utf-8")
        temporary.replace(destination)
        return storage_key

    def load(self, storage_key: str) -> bytes:
        try:
            return self._resolve(storage_key).read_bytes()
        except OSError as exception:
            raise ApiError(
                status_code=404,
                code="HTML_NOT_FOUND",
                message="O HTML gerado não foi encontrado.",
            ) from exception

    def delete(self, storage_key: str) -> None:
        destination = self._resolve(storage_key)
        if destination.exists():
            destination.unlink()


class S3HtmlStorage:
    def __init__(self, *, client, bucket: str) -> None:
        self.client = client
        self.bucket = bucket

    def save(self, job_id: str, html: str) -> str:
        storage_key = f"html/{job_id}.html"
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=storage_key,
                Body=html.encode(),
                ContentType="text/html; charset=utf-8",
            )
        except (BotoCoreError, ClientError) as exception:
            raise ApiError(
                status_code=503,
                code="STORAGE_UNAVAILABLE",
                message="O armazenamento de documentos está indisponível.",
            ) from exception
        return storage_key

    def load(self, storage_key: str) -> bytes:
        if not storage_key.startswith("html/") or not storage_key.endswith(".html"):
            raise ApiError(
                status_code=400,
                code="INVALID_STORAGE_KEY",
                message="A referência do HTML é inválida.",
            )
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=storage_key)
            return response["Body"].read()
        except (BotoCoreError, ClientError, KeyError) as exception:
            raise ApiError(
                status_code=404,
                code="HTML_NOT_FOUND",
                message="O HTML gerado não foi encontrado.",
            ) from exception

    def delete(self, storage_key: str) -> None:
        if not storage_key.startswith("html/") or not storage_key.endswith(".html"):
            raise ApiError(
                status_code=400,
                code="INVALID_STORAGE_KEY",
                message="A referência do HTML é inválida.",
            )
        try:
            self.client.delete_object(Bucket=self.bucket, Key=storage_key)
        except (BotoCoreError, ClientError) as exception:
            raise ApiError(
                status_code=503,
                code="STORAGE_UNAVAILABLE",
                message="O armazenamento de documentos está indisponível.",
            ) from exception


class DatabaseHtmlStorage:
    prefix = "database/"

    def save(self, job_id: str, html: str) -> str:
        with get_session_factory()() as session:
            job = session.get(JobRecord, job_id)
            if job is None:
                raise ApiError(
                    status_code=404,
                    code="JOB_NOT_FOUND",
                    message="O job solicitado não foi encontrado.",
                )
            job.html_content = html
            session.commit()
        return f"{self.prefix}{job_id}.html"

    def load(self, storage_key: str) -> bytes:
        if not storage_key.startswith(self.prefix) or not storage_key.endswith(".html"):
            raise ApiError(
                status_code=400,
                code="INVALID_STORAGE_KEY",
                message="A referência do HTML é inválida.",
            )
        job_id = storage_key.removeprefix(self.prefix).removesuffix(".html")
        with get_session_factory()() as session:
            job = session.get(JobRecord, job_id)
            if job is None or job.html_content is None:
                raise ApiError(
                    status_code=404,
                    code="HTML_NOT_FOUND",
                    message="O HTML gerado não foi encontrado.",
                )
            return job.html_content.encode()

    def delete(self, storage_key: str) -> None:
        job_id = storage_key.removeprefix(self.prefix).removesuffix(".html")
        with get_session_factory()() as session:
            job = session.get(JobRecord, job_id)
            if job is not None:
                job.html_content = None
                session.commit()


def create_html_storage(settings: Settings) -> HtmlStorage:
    if settings.html_storage_backend == "database":
        return DatabaseHtmlStorage()
    if settings.html_storage_backend == "local":
        return LocalHtmlStorage(settings.generated_html_root)
    if settings.html_storage_backend == "s3":
        return S3HtmlStorage(
            client=create_s3_client(settings),
            bucket=settings.storage_bucket,
        )
    raise ApiError(
        status_code=503,
        code="STORAGE_NOT_CONFIGURED",
        message="O backend de armazenamento não é suportado.",
    )
