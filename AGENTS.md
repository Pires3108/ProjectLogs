# Repository Guidelines

## Project Structure & Module Organization

AtaViva is now scoped to the plugin/CLI only — there is no web app, API, or
database in this repository.

- `backend/app/cli.py` — the entry point; `render-analysis` generates the
  HTML document from a `StructuredAnalysis` JSON.
- `backend/app/analysis/` — `models.py` (the `StructuredAnalysis` schema) and
  `prompt.py` (the extraction rules Claude follows when acting as the
  skill's analyst).
- `backend/app/documents/` — profile/toggle rules, the Jinja2 HTML generator,
  and templates.
- `backend/tests/` — unit tests alongside the code they cover.
- `.claude/skills/ataviva-cli-analyze/` — the Claude Code skill that drives
  the local, no-API extraction-and-render flow.
- `.claude-plugin/plugin.json` — the plugin manifest; makes this repo
  installable via `claude plugin install`.

Do not commit generated HTML, uploaded media, credentials, or local runtime
data.

## Build, Test, and Development Commands

- `cd backend && uv sync --extra dev` — install dependencies.
- `cd backend && uv run pytest` — run tests.
- `cd backend && uv run ruff check .` — lint.
- `cd backend && uv run python -m app.cli render-analysis --analysis ... --perfil ... --toggles ... --output ...` — generate a document.

## Coding Style & Naming Conventions

Four spaces for Python. `snake_case` for modules/functions, `PascalCase` for
classes. Keep JSON fields consistent with the existing Portuguese contract
(for example, `perfil` and `linha_do_tempo`). Ruff is the linter/formatter.

## Testing Guidelines

Cover profile/toggle validation and HTML sections with unit tests. Name
tests `test_*.py`. Include a regression test with every bug fix.

## Commit & Pull Request Guidelines

Use concise imperative commits, optionally following Conventional Commits:
`feat: add document normalizer` or `fix: handle invalid profile toggle`.
Keep commits focused. Pull requests should summarize behavior, list
verification performed, and note configuration changes. Never expose API
keys, meeting content, or personally identifiable information in fixtures,
logs, or review artifacts.
