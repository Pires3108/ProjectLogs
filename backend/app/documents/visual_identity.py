"""Experimental: reuse the visual identity (CSS custom properties) of a reference
AtaViva document, instead of the default tokens defined in ``base.html``.

Gated by ``Settings.feature_visual_identity``. Only known token names are
accepted and values are constrained to plain CSS literals — no ``url()``,
``@import`` or nested braces — since the result is spliced back into a
``<style>`` block.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from app.errors import ApiError

_ALLOWED_TOKENS = frozenset(
    {
        "ink",
        "ink-2",
        "muted",
        "paper",
        "surface",
        "line",
        "line-soft",
        "accent",
        "accent-soft",
        "spark",
        "good",
        "warn",
        "danger",
        "radius",
        "sans",
        "display",
        "mono",
    }
)

_ROOT_BLOCK = re.compile(r":root\s*{([^}]*)}")
_DECLARATION = re.compile(r"--([a-z0-9-]+)\s*:\s*([^;{}]+);")
_UNSAFE_VALUE = re.compile(r"url\(|@import|expression\(|</", re.IGNORECASE)


@dataclass(frozen=True)
class VisualIdentity:
    source_path: Path
    variables: dict[str, str]


def extract_visual_identity(html_text: str, *, source_path: Path) -> VisualIdentity:
    root_match = _ROOT_BLOCK.search(html_text)
    if root_match is None:
        raise ApiError(
            status_code=422,
            code="VISUAL_IDENTITY_NOT_FOUND",
            message=f"Não foi possível encontrar tokens de identidade visual em '{source_path}'.",
        )
    variables: dict[str, str] = {}
    for name, value in _DECLARATION.findall(root_match.group(1)):
        value = value.strip()
        if name not in _ALLOWED_TOKENS or not value or _UNSAFE_VALUE.search(value):
            continue
        variables[name] = value
    if not variables:
        raise ApiError(
            status_code=422,
            code="VISUAL_IDENTITY_NOT_FOUND",
            message=f"Não foi possível encontrar tokens de identidade visual em '{source_path}'.",
        )
    return VisualIdentity(source_path=source_path, variables=variables)


def resolve_visual_identity_reference(
    *, document: str | None, directory: str | None
) -> VisualIdentity:
    if document and directory:
        raise ApiError(
            status_code=422,
            code="VISUAL_IDENTITY_AMBIGUOUS_REFERENCE",
            message="Informe apenas um documento ou um diretório de referência, não os dois.",
        )
    if document:
        path = Path(document)
        if not path.is_file():
            raise ApiError(
                status_code=422,
                code="VISUAL_IDENTITY_REFERENCE_NOT_FOUND",
                message=f"O documento de referência '{document}' não foi encontrado.",
            )
        return extract_visual_identity(path.read_text(encoding="utf-8"), source_path=path)
    if directory:
        directory_path = Path(directory)
        candidates = sorted(
            (p for p in directory_path.glob("*.html") if p.is_file()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            raise ApiError(
                status_code=422,
                code="VISUAL_IDENTITY_REFERENCE_NOT_FOUND",
                message=f"Nenhum documento HTML foi encontrado em '{directory}'.",
            )
        last_error: ApiError | None = None
        for candidate in candidates:
            try:
                return extract_visual_identity(
                    candidate.read_text(encoding="utf-8"), source_path=candidate
                )
            except ApiError as exception:
                last_error = exception
        assert last_error is not None
        raise last_error
    raise ApiError(
        status_code=422,
        code="VISUAL_IDENTITY_MISSING_REFERENCE",
        message="Informe um documento ou um diretório de referência.",
    )


def build_override_style(identity: VisualIdentity) -> str:
    declarations = "".join(
        f"--{name}:{value};" for name, value in sorted(identity.variables.items())
    )
    return f":root{{{declarations}}}"
