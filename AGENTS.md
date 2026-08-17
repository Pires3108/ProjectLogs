# Repository Guidelines

## Project Structure & Module Organization

This repository is currently in the planning phase. `backlog-projeto.md` is the source of truth for scope, architecture, error contracts, and the sprint plan. As implementation begins, keep the proposed services separated:

- `frontend/` — Next.js UI for uploads, profile/toggle selection, and job status.
- `backend/` — FastAPI application, ingestion pipeline, provider abstraction, and HTML generation.
- `tests/` — integration and end-to-end tests; unit tests may live beside each service.
- `infra/` — Docker, CI/CD, database, Redis, and storage configuration.
- `docs/` — OpenAPI artifacts and architectural decisions.

Do not commit generated HTML, uploaded media, credentials, or local runtime data.

## Build, Test, and Development Commands

No runnable application or package manifest exists yet. Add exact commands to the root `README.md` when scaffolding a service. Prefer predictable entry points such as:

- `docker compose up --build` — start the complete local stack.
- `cd backend && pytest` — run backend tests.
- `cd frontend && npm test` — run frontend tests.
- `cd frontend && npm run lint` — check frontend style.

Commands above are target conventions, not yet implemented; keep them current as tooling is added.

## Coding Style & Naming Conventions

Use four spaces for Python and two spaces for TypeScript, JSON, and YAML. Follow `snake_case` for Python modules/functions, `PascalCase` for React components and Python classes, and `camelCase` for TypeScript variables. Keep API JSON fields consistent with the Portuguese contract where already defined (for example, `perfil` and `linha_do_tempo`). Use automated formatters and linters configured by each service; recommended defaults are Ruff for Python and ESLint/Prettier for TypeScript.

## Testing Guidelines

Cover parsers, document normalization, profile/toggle validation, and HTML sections with unit tests. Mock Gemini and Groq in integration tests, including `429` fallback behavior. Add contract tests against OpenAPI and E2E coverage for upload-to-download flows. Name Python tests `test_*.py`; use `*.test.ts(x)` for frontend tests. Include regression tests with every bug fix.

## Commit & Pull Request Guidelines

There is no Git history establishing a convention. Use concise imperative commits, optionally following Conventional Commits: `feat: add document normalizer` or `fix: handle invalid profile toggle`. Keep commits focused. Pull requests should summarize behavior, reference the relevant backlog item or issue, list verification performed, and note API/configuration changes. Include screenshots for UI or generated-HTML changes. Never expose API keys, meeting content, or personally identifiable information in fixtures, logs, or review artifacts.
