from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ingests_multiple_text_sources() -> None:
    response = client.post(
        "/v1/ingestions",
        files=[
            (
                "fontes",
                ("pauta.md", b"# Pauta\n\nVamos definir as proximas entregas.", "text/markdown"),
            ),
            (
                "fontes",
                (
                    "reuniao.srt",
                    b"1\n00:00:00,000 --> 00:00:02,000\nPrimeira decisao importante\n",
                    "application/x-subrip",
                ),
            ),
        ],
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["total_fontes"] == 2
    assert payload["pronto_para_analise"] is True
    assert payload["fontes"][0]["id"]
    assert payload["fontes"][0]["texto_normalizado"].startswith("Pauta")


def test_marks_media_as_requiring_transcription() -> None:
    response = client.post(
        "/v1/ingestions",
        files=[("fontes", ("gravacao.mp3", b"ID3synthetic-audio-placeholder", "audio/mpeg"))],
    )

    assert response.status_code == 201
    assert response.json()["pronto_para_analise"] is False
    assert response.json()["fontes"][0]["requer_transcricao"] is True


def test_rejects_media_with_spoofed_extension() -> None:
    response = client.post(
        "/v1/ingestions",
        files=[("fontes", ("gravacao.mp4", b"not really a video", "video/mp4"))],
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_CONTENT"


def test_detects_read_ai_transcript_export() -> None:
    content = (
        "Reunião sintética\nseg., 17 de ago. de 2026\n\n"
        "0:00 - Pessoa Exemplo\nEsta é uma fala sintética suficientemente longa.\n"
    ).encode()

    response = client.post(
        "/v1/ingestions",
        files=[("fontes", ("transcricao.txt", content, "text/plain"))],
    )

    assert response.status_code == 201
    assert response.json()["fontes"][0]["formato"] == "read.ai"
    assert response.json()["fontes"][0]["texto_normalizado"].startswith("Pessoa Exemplo:")


def test_rejects_unsupported_format_with_standard_error() -> None:
    response = client.post(
        "/v1/ingestions",
        files=[("fontes", ("conteudo.exe", b"synthetic", "application/octet-stream"))],
        headers={"x-request-id": "request-test"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "UNSUPPORTED_FORMAT",
            "message": "O formato do arquivo não é suportado.",
            "details": {"filename": "conteudo.exe", "extension": ".exe"},
            "request_id": "request-test",
        }
    }


def test_rejects_empty_file() -> None:
    response = client.post(
        "/v1/ingestions",
        files=[("fontes", ("vazio.txt", b"", "text/plain"))],
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INSUFFICIENT_CONTENT"


def test_rejects_file_over_configured_limit(monkeypatch) -> None:
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "max_document_bytes", 4)
    try:
        response = client.post(
            "/v1/ingestions",
            files=[("fontes", ("grande.txt", b"cinco", "text/plain"))],
        )
    finally:
        monkeypatch.undo()

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"
