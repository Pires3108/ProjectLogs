import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import ApiKeyRecord
from app.db.session import get_db_session
from app.errors import ApiError

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(frozen=True, slots=True)
class ApiPrincipal:
    id: str
    name: str


def digest_api_key(raw_key: str, pepper: str) -> str:
    return hmac.new(pepper.encode(), raw_key.encode(), hashlib.sha256).hexdigest()


def issue_api_key(
    name: str, pepper: str, expires_at: datetime | None = None
) -> tuple[str, ApiKeyRecord]:
    raw_key = f"ataviva_{secrets.token_urlsafe(32)}"
    record = ApiKeyRecord(
        name=name,
        key_prefix=raw_key[:20],
        key_digest=digest_api_key(raw_key, pepper),
        expires_at=expires_at,
    )
    return raw_key, record


def require_api_key(
    raw_key: Annotated[str | None, Security(api_key_header)],
    session: Annotated[Session, Depends(get_db_session)],
) -> ApiPrincipal:
    if not raw_key:
        raise _unauthorized("API_KEY_MISSING", "Informe a API Key no cabeçalho X-API-Key.")
    settings = get_settings()
    digest = digest_api_key(raw_key, settings.api_key_pepper.get_secret_value())
    record = session.scalar(select(ApiKeyRecord).where(ApiKeyRecord.key_digest == digest))
    now = datetime.now(UTC)
    if record is None or record.revoked_at is not None:
        raise _unauthorized("API_KEY_INVALID", "A API Key é inválida ou foi revogada.")
    if record.expires_at is not None:
        expiration = record.expires_at
        if expiration.tzinfo is None:
            expiration = expiration.replace(tzinfo=UTC)
        if expiration <= now:
            raise _unauthorized("API_KEY_EXPIRED", "A API Key está expirada.")
    record.last_used_at = now
    session.commit()
    return ApiPrincipal(id=record.id, name=record.name)


def _unauthorized(code: str, message: str) -> ApiError:
    return ApiError(status_code=401, code=code, message=message)
