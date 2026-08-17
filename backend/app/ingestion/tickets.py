import base64
import hashlib
import hmac
import json
import time
from dataclasses import asdict, dataclass

from app.errors import ApiError


@dataclass(frozen=True, slots=True)
class UploadTicket:
    source_id: str
    api_key_id: str
    filename: str
    extension: str
    content_type: str
    size_bytes: int
    expires_at: int


def sign_ticket(ticket: UploadTicket, secret: str) -> str:
    payload = json.dumps(asdict(ticket), separators=(",", ":"), sort_keys=True).encode()
    encoded = base64.urlsafe_b64encode(payload).rstrip(b"=")
    signature = hmac.new(secret.encode(), encoded, hashlib.sha256).digest()
    return f"{encoded.decode()}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def verify_ticket(value: str, secret: str) -> UploadTicket:
    try:
        encoded, supplied = value.split(".", 1)
        expected = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest()
        signature = base64.urlsafe_b64decode(supplied + "=" * (-len(supplied) % 4))
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        payload = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        ticket = UploadTicket(**json.loads(payload))
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exception:
        raise ApiError(
            status_code=400,
            code="INVALID_UPLOAD_TICKET",
            message="O ticket de upload é inválido.",
        ) from exception
    if ticket.expires_at < int(time.time()):
        raise ApiError(
            status_code=410,
            code="UPLOAD_TICKET_EXPIRED",
            message="O ticket de upload expirou.",
        )
    return ticket
