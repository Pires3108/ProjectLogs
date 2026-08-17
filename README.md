# AtaViva

Aplicação para transformar fontes de reuniões em documentação estruturada. O projeto está sendo implementado conforme o `backlog-projeto.md`.

## Estado atual

Sprints 0 a 8: pipeline assíncrono, API/frontend, fallback, rate limiting, métricas, validação defensiva e upload direto de arquivos grandes. Consulte `docs/sprints/` para critérios e evidências. O caminho prioritário sem cartão está em `infra/deploy-sem-cartao.md`; o caminho serverless mais robusto, mas com billing habilitado, permanece em `infra/deploy-gratuito.md`.

## Pré-requisitos

- Docker 28+ com Docker Compose v2
- Para desenvolvimento sem Docker: Python 3.12+ e Node.js 22+

## Executar a stack

```sh
copy .env.example .env
docker compose up --build
```

- Site: http://localhost:3000
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc
- MinIO: http://localhost:9001

## Backend

```sh
cd backend
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"
.venv/Scripts/pytest
.venv/Scripts/ruff check .
```

Com `uv`, o fluxo equivalente é `cd backend && uv sync --extra dev && uv run pytest`.

### Banco e API Key

```sh
cd backend
uv run alembic upgrade head
uv run python -m app.cli create-api-key --name "desenvolvimento local"
```

A chave é exibida uma única vez. O banco armazena somente seu HMAC. Defina um
`API_KEY_PEPPER` forte e estável antes de emitir chaves fora do desenvolvimento.

A limpeza por retenção é deliberadamente manual até a política ser aprovada. Ela começa em modo
simulação e exige uma data explícita com fuso:

```sh
uv run python -m app.cli cleanup-jobs --before 2026-09-01T00:00:00+00:00
uv run python -m app.cli cleanup-jobs --before 2026-09-01T00:00:00+00:00 --execute
```

### Ingestão

```sh
curl -X POST http://localhost:8000/v1/ingestions \
  -F "fontes=@pauta.md" \
  -F "fontes=@transcricao.srt"
```

Documentos e transcrições retornam texto normalizado. Áudio e vídeo recebem um identificador
e ficam marcados com `requer_transcricao: true` para processamento na etapa seguinte.

### Criar e consultar um job

```sh
curl -X POST http://localhost:8000/v1/jobs \
  -H "X-API-Key: $ATAVIVA_API_KEY" \
  -F "perfil=estudo" \
  -F 'toggles={"exercicios":true,"glossario":true}' \
  -F "fontes=@pauta.md"

curl http://localhost:8000/v1/jobs/JOB_ID \
  -H "X-API-Key: $ATAVIVA_API_KEY"
```

O retorno inicial usa `queued`. Chaves só enxergam seus próprios jobs; recursos de outra chave
também retornam `404`.

Em Linux/macOS, use `.venv/bin/` no lugar de `.venv/Scripts/`.

## Frontend

```sh
cd frontend
npm ci
npm run lint
npm test
npm run build
```

## Contrato

O contrato versionado inicial está em `docs/openapi.yaml`. Durante o desenvolvimento, a documentação gerada pela aplicação em `/openapi.json` é a referência executável e deve permanecer compatível com esse artefato.

## Segurança de dados

Não adicione uploads, HTMLs gerados, credenciais, conteúdo de reuniões nem dados pessoais ao repositório. Use apenas fixtures sintéticas nos testes.
