# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project scope

AtaViva is now scoped to the plugin/CLI only — there is no web app, API, worker, or
database in this repository. All prior FastAPI/Celery/Next.js/Postgres code (backend
`routes.py`, `jobs/`, `ingestion/`, `db/`, `auth/`, `transcription/`, the `frontend/`
directory, `docker-compose.yml`, `firebase.json`, Alembic migrations) has been removed.
New work should target the CLI and the Claude Code skill, not reintroduce a web
service — this is a deliberate direction, not an in-progress deletion to "finish."

The actual analysis step (turning a meeting/document source into a `StructuredAnalysis`)
is performed by Claude directly in conversation via the
`.claude/skills/ataviva-cli-analyze` skill — there is no Gemini/Groq API call anywhere
in this codebase anymore. The Python code only validates and renders the JSON Claude
produces into HTML.

## Commands

```sh
cd backend
uv sync --extra dev          # install deps
uv run pytest                # run tests
uv run pytest tests/test_html_generator.py::test_name  # run a single test
uv run ruff check .          # lint (also the CI gate)
```

Generate a document from an already-produced `StructuredAnalysis` JSON:

```sh
uv run python -m app.cli render-analysis \
  --analysis analise.json \
  --perfil estudo \
  --toggles '{"exercicios": true, "glossario": true}' \
  --output documento.html
```

CI (`.github/workflows/ci.yml`) runs `ruff check .` then `pytest` from `backend/` on
Python 3.12 — no separate frontend/lint job exists.

## Architecture

Everything lives under `backend/app/`:

- **`cli.py`** — the only entry point (`argparse`-based). `render_analysis()` loads the
  analysis JSON, validates the profile/toggle configuration, resolves an optional
  experimental visual-identity override, calls `HtmlGenerator`, and writes the HTML file.
  There is no HTTP server, no job queue, no persistence — this is a synchronous, local
  transform.
- **`analysis/models.py`** — `StructuredAnalysis` and its nested Pydantic models
  (`WorkItem`, `GlossaryTerm`, `TimelineEvent`, `ResponsibilityEntry`,
  `VisualDefinition`). This is the exact contract Claude must produce when acting as
  the analyst. All models use `StrictModel` (`extra="forbid"`) — fields are Portuguese
  (`objetivo`, `resumo`, `itens`, `linha_do_tempo`, etc.) and must not be renamed to
  English.
- **`analysis/prompt.py`** — `SYSTEM_INSTRUCTION` and `build_analysis_prompt` are the
  extraction rules the skill points Claude at (only use source-grounded facts, mark
  unclear values in `termos_incertos`, keep `objetivo` a short title, etc.). This file
  is read as instructions by the skill, not executed against an external LLM.
- **`documents/configuration.py`** — `PROFILE_RULES` defines the three document
  profiles (`estudo`, `organizacao`, `backlog`), each with required sections, tone, and
  an allow-list of `ContentToggle`s. `validate_configuration()` silently disables (with
  a warning, not an error) any toggle not permitted for the chosen profile — this is
  intentional, expected behavior, not a bug to "fix."
- **`documents/html.py`** — `HtmlGenerator` renders one of the Jinja2 templates in
  `documents/templates/` (`estudo.html`, `organizacao.html`, `backlog.html`, sharing
  `base.html`). It also builds Mermaid flowchart/diagram source from `visuais` (only
  when the corresponding toggle is enabled and the visual has both nodes and
  connections) and, for the `estudo` profile with `exercicios` enabled, generates a
  multiple-choice quiz from work items/glossary terms using distractors sampled from
  other answers.
- **`documents/visual_identity.py`** — experimental, gated behind
  `Settings.feature_visual_identity`. Extracts CSS custom-property tokens (`--accent`, `--ink`, etc.) from the `:root`
  block of a prior AtaViva HTML document and lets a new document reuse that palette.
  Only an explicit allow-list of token names is accepted, and values are rejected if
  they contain `url()`, `@import`, or other unsafe constructs, since the result is
  spliced back into a `<style>` block. When the feature flag is off, the CLI accepts
  the `--identidade-visual-*` flags but no-ops with a printed warning — that is the
  expected behavior of a disabled experimental flag, not an error.
- **`config.py`** — `Settings` (pydantic-settings) reads `.env`; only two settings
  exist: `mermaid_asset_path` and `feature_visual_identity`.
- **`models.py`** — shared enums used across both `analysis` and `documents`:
  `DocumentProfile` and `ContentToggle`.
- **`errors.py`** — `ApiError`, a plain exception carrying `status_code`/`code`/
  `message`, reused as a generic domain error even though there is no HTTP layer left
  to translate it into a response.

The Mermaid runtime asset (`app/static/vendor/mermaid.min.js`) is not vendored in this
checkout — it's normally fetched during a Docker build. If a document needs
flowcharts/diagrams and the vendored file is missing, fetch `mermaid.min.js` some other
way (e.g. `npm install mermaid` in a scratch dir) and pass `--mermaid-asset`; otherwise
`render-analysis` fails with `MERMAID_ASSET_UNAVAILABLE`.

## Plugin manifest

`.claude-plugin/plugin.json` makes this repo installable as a Claude Code plugin
(`claude plugin install --plugin-dir .` or `--plugin-url <archive-zip-url>`). Its
`skills` field points at the existing `.claude/skills/` directory rather than a
top-level `skills/`, so the skill still auto-loads when someone opens this repo
directly, without requiring a plugin install. Bump `version` here on every
user-visible change to the skill or CLI contract.

`.claude-plugin/marketplace.json` makes the same repo discoverable via
`/plugin marketplace add Pires3108/ProjectLogs` + `/plugin install ataviva@ataviva`
(without it, a direct repo isn't listed by `/plugin marketplace add` even though
`--plugin-dir`/`--plugin-url` installs still work). Its single plugin entry sources
from `"./"` (the marketplace root, i.e. this repo), so `plugin.json` stays the
single source of truth for components — keep the `version` in sync between the two
files rather than setting it in both, since a stale `plugin.json` version silently
overrides the marketplace entry's. Run `claude plugin validate .` after editing
either file.

## The skill

`.claude/skills/ataviva-cli-analyze/SKILL.md` drives the actual product flow: it tells
Claude to re-read `analysis/prompt.py`, `analysis/models.py`, and
`documents/configuration.py` before extracting (never trust a previous session's
memory of the schema/rules), do the extraction itself from the user's source, write the
JSON to a scratch file, and invoke `render-analysis`. It also has explicit guidance on
where to save the resulting HTML (prefer an existing docs folder in the source's host
project over defaulting to `Downloads`). Read this file before changing the extraction
contract or the CLI's argument surface, since the two must stay in sync.

## Coding conventions

Four-space Python, `snake_case` modules/functions, `PascalCase` classes. JSON/schema
field names follow the existing Portuguese contract (`perfil`, `linha_do_tempo`, etc.)
— do not translate them. Ruff (`select = ["E", "F", "I", "UP", "B"]`) is both linter and
style authority.

Never commit generated HTML, uploaded media, credentials, or real meeting
content/PII — tests use synthetic fixtures only (see `backend/tests/analysis_fixtures.py`).
