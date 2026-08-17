from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol
from uuid import UUID, uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import Settings
from app.errors import ApiError
from app.ingestion.types import SUPPORTED_SOURCE_TYPES


class SourceStorage(Protocol):
    def save(self, extension: str, content: bytes) -> str: ...

    def delete(self, source_id: str, extension: str) -> None: ...

    def materialize(self, source_id: str, extension: str) -> AbstractContextManager[Path]: ...

    def create_upload(
        self, source_id: str, extension: str, content_type: str, expires: int
    ) -> str: ...

    def size(self, source_id: str, extension: str) -> int: ...


class LocalSourceStorage:
    """Local development storage behind a replaceable boundary."""

    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()

    def save(self, extension: str, content: bytes) -> str:
        source_id = str(uuid4())
        self.root.mkdir(parents=True, exist_ok=True)
        destination = (self.root / f"{source_id}{extension}").resolve()
        if self.root not in destination.parents:
            raise ValueError("Invalid storage destination")
        destination.write_bytes(content)
        return source_id

    def resolve(self, source_id: str, extension: str) -> Path:
        try:
            canonical_id = str(UUID(source_id))
        except ValueError as exception:
            raise ApiError(
                status_code=400,
                code="INVALID_SOURCE_ID",
                message="O identificador da fonte é inválido.",
            ) from exception
        if extension not in SUPPORTED_SOURCE_TYPES:
            raise ApiError(
                status_code=400,
                code="UNSUPPORTED_FORMAT",
                message="O formato do arquivo não é suportado.",
                details={"extension": extension},
            )
        source = (self.root / f"{canonical_id}{extension}").resolve()
        if self.root not in source.parents:
            raise ApiError(
                status_code=400,
                code="INVALID_SOURCE_ID",
                message="O identificador da fonte é inválido.",
            )
        if not source.is_file():
            raise ApiError(
                status_code=404,
                code="SOURCE_NOT_FOUND",
                message="A fonte solicitada não foi encontrada.",
            )
        return source

    def delete(self, source_id: str, extension: str) -> None:
        try:
            source = self.resolve(source_id, extension)
        except ApiError as exception:
            if exception.code == "SOURCE_NOT_FOUND":
                return
            raise
        source.unlink()

    @contextmanager
    def materialize(self, source_id: str, extension: str) -> Iterator[Path]:
        yield self.resolve(source_id, extension)

    def create_upload(self, source_id: str, extension: str, content_type: str, expires: int) -> str:
        raise ApiError(
            status_code=503,
            code="DIRECT_UPLOAD_UNAVAILABLE",
            message="O upload direto exige armazenamento S3/R2.",
        )

    def size(self, source_id: str, extension: str) -> int:
        return self.resolve(source_id, extension).stat().st_size


class S3SourceStorage:
    def __init__(self, *, client, bucket: str) -> None:
        self.client = client
        self.bucket = bucket

    @staticmethod
    def key(source_id: str, extension: str) -> str:
        canonical_id = str(UUID(source_id))
        if extension not in SUPPORTED_SOURCE_TYPES:
            raise ApiError(
                status_code=400,
                code="UNSUPPORTED_FORMAT",
                message="O formato do arquivo não é suportado.",
            )
        return f"sources/{canonical_id}{extension}"

    def save(self, extension: str, content: bytes) -> str:
        source_id = str(uuid4())
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=self.key(source_id, extension),
                Body=content,
            )
        except (BotoCoreError, ClientError) as exception:
            raise ApiError(
                status_code=503,
                code="STORAGE_UNAVAILABLE",
                message="O armazenamento de arquivos está indisponível.",
            ) from exception
        return source_id

    def create_upload(self, source_id: str, extension: str, content_type: str, expires: int) -> str:
        try:
            return self.client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": self.key(source_id, extension),
                    "ContentType": content_type,
                },
                ExpiresIn=expires,
            )
        except (BotoCoreError, ClientError) as exception:
            raise ApiError(
                status_code=503,
                code="STORAGE_UNAVAILABLE",
                message="O armazenamento de arquivos está indisponível.",
            ) from exception

    def size(self, source_id: str, extension: str) -> int:
        try:
            result = self.client.head_object(Bucket=self.bucket, Key=self.key(source_id, extension))
            return int(result["ContentLength"])
        except (BotoCoreError, ClientError, KeyError) as exception:
            raise ApiError(
                status_code=422,
                code="UPLOAD_NOT_FOUND",
                message="O upload não foi concluído no armazenamento.",
            ) from exception

    def delete(self, source_id: str, extension: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=self.key(source_id, extension))
        except (BotoCoreError, ClientError) as exception:
            raise ApiError(
                status_code=503,
                code="STORAGE_UNAVAILABLE",
                message="O armazenamento de arquivos está indisponível.",
            ) from exception

    @contextmanager
    def materialize(self, source_id: str, extension: str) -> Iterator[Path]:
        with TemporaryDirectory(prefix="ataviva-source-") as directory:
            destination = Path(directory) / f"source{extension}"
            try:
                self.client.download_file(
                    self.bucket,
                    self.key(source_id, extension),
                    str(destination),
                )
            except (BotoCoreError, ClientError) as exception:
                raise ApiError(
                    status_code=503,
                    code="STORAGE_UNAVAILABLE",
                    message="O armazenamento de arquivos está indisponível.",
                ) from exception
            yield destination


def create_s3_client(settings: Settings):
    if settings.storage_access_key is None or settings.storage_secret_key is None:
        raise ApiError(
            status_code=503,
            code="STORAGE_NOT_CONFIGURED",
            message="O armazenamento de objetos não está configurado.",
        )
    return boto3.client(
        "s3",
        endpoint_url=settings.storage_endpoint,
        aws_access_key_id=settings.storage_access_key.get_secret_value(),
        aws_secret_access_key=settings.storage_secret_key.get_secret_value(),
        region_name=settings.storage_region,
    )


def create_source_storage(settings: Settings) -> SourceStorage:
    if settings.storage_backend == "local":
        return LocalSourceStorage(settings.upload_root)
    if settings.storage_backend == "s3":
        return S3SourceStorage(
            client=create_s3_client(settings),
            bucket=settings.storage_bucket,
        )
    raise ApiError(
        status_code=503,
        code="STORAGE_NOT_CONFIGURED",
        message="O backend de armazenamento não é suportado.",
    )
