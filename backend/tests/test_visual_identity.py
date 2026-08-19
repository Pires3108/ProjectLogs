from pathlib import Path

import pytest

from app.documents.visual_identity import (
    build_override_style,
    extract_visual_identity,
    resolve_visual_identity_reference,
)
from app.errors import ApiError

_REFERENCE_HTML = """
<html><head><style>
:root { --accent:#0e6b57; --accent-soft:#d9efe8; --spark:#af501e; --ink:#111111; }
</style></head><body></body></html>
"""


def test_extract_visual_identity_reads_allowed_tokens(tmp_path: Path) -> None:
    path = tmp_path / "referencia.html"
    identity = extract_visual_identity(_REFERENCE_HTML, source_path=path)

    assert identity.variables == {
        "accent": "#0e6b57",
        "accent-soft": "#d9efe8",
        "spark": "#af501e",
        "ink": "#111111",
    }


def test_extract_visual_identity_drops_unknown_and_unsafe_tokens(tmp_path: Path) -> None:
    html = """
    <style>:root {
      --accent:#0e6b57;
      --content:920px;
      --spark:url(https://evil.example/track.png);
    }</style>
    """
    identity = extract_visual_identity(html, source_path=tmp_path / "referencia.html")

    assert identity.variables == {"accent": "#0e6b57"}


def test_extract_visual_identity_raises_when_no_root_block(tmp_path: Path) -> None:
    with pytest.raises(ApiError) as excinfo:
        extract_visual_identity("<html></html>", source_path=tmp_path / "referencia.html")

    assert excinfo.value.code == "VISUAL_IDENTITY_NOT_FOUND"


def test_resolve_visual_identity_reference_rejects_both_document_and_directory(
    tmp_path: Path,
) -> None:
    with pytest.raises(ApiError) as excinfo:
        resolve_visual_identity_reference(document=str(tmp_path), directory=str(tmp_path))

    assert excinfo.value.code == "VISUAL_IDENTITY_AMBIGUOUS_REFERENCE"


def test_resolve_visual_identity_reference_from_document(tmp_path: Path) -> None:
    path = tmp_path / "referencia.html"
    path.write_text(_REFERENCE_HTML, encoding="utf-8")

    identity = resolve_visual_identity_reference(document=str(path), directory=None)

    assert identity.source_path == path


def test_resolve_visual_identity_reference_from_directory_picks_most_recent(
    tmp_path: Path,
) -> None:
    older = tmp_path / "antigo.html"
    older.write_text(_REFERENCE_HTML, encoding="utf-8")
    newer = tmp_path / "novo.html"
    newer.write_text(_REFERENCE_HTML.replace("#0e6b57", "#3b4fc7"), encoding="utf-8")
    import os
    import time

    now = time.time()
    os.utime(older, (now - 100, now - 100))
    os.utime(newer, (now, now))

    identity = resolve_visual_identity_reference(document=None, directory=str(tmp_path))

    assert identity.source_path == newer
    assert identity.variables["accent"] == "#3b4fc7"


def test_resolve_visual_identity_reference_missing_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(ApiError) as excinfo:
        resolve_visual_identity_reference(document=None, directory=str(tmp_path / "vazio"))

    assert excinfo.value.code == "VISUAL_IDENTITY_REFERENCE_NOT_FOUND"


def test_resolve_visual_identity_reference_requires_one_argument() -> None:
    with pytest.raises(ApiError) as excinfo:
        resolve_visual_identity_reference(document=None, directory=None)

    assert excinfo.value.code == "VISUAL_IDENTITY_MISSING_REFERENCE"


def test_build_override_style_is_deterministic_and_safe(tmp_path: Path) -> None:
    identity = extract_visual_identity(_REFERENCE_HTML, source_path=tmp_path / "r.html")

    style = build_override_style(identity)

    assert style == ":root{--accent:#0e6b57;--accent-soft:#d9efe8;--ink:#111111;--spark:#af501e;}"
