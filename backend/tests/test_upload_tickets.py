import time

import pytest

from app.errors import ApiError
from app.ingestion.tickets import UploadTicket, sign_ticket, verify_ticket


def ticket(**changes) -> UploadTicket:
    values = {
        "source_id": "46b91c44-1cd0-49fe-a915-e7b721fd3855",
        "api_key_id": "owner",
        "filename": "meeting.mp4",
        "extension": ".mp4",
        "content_type": "video/mp4",
        "size_bytes": 206_175_845,
        "expires_at": int(time.time()) + 60,
    }
    values.update(changes)
    return UploadTicket(**values)


def test_signed_ticket_round_trip() -> None:
    signed = sign_ticket(ticket(), "secret")
    assert verify_ticket(signed, "secret").size_bytes == 206_175_845


def test_ticket_rejects_tampering_and_expiration() -> None:
    with pytest.raises(ApiError) as invalid:
        verify_ticket(sign_ticket(ticket(), "secret") + "x", "secret")
    assert invalid.value.code == "INVALID_UPLOAD_TICKET"
    with pytest.raises(ApiError) as expired:
        verify_ticket(sign_ticket(ticket(expires_at=1), "secret"), "secret")
    assert expired.value.code == "UPLOAD_TICKET_EXPIRED"
