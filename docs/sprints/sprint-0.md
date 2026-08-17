# Sprint 0 — Fundação

## Escopo entregue

- Estrutura inicial de `backend/`, `frontend/`, `infra` via Compose e `docs/`.
- API FastAPI com health check, IDs de requisição e catálogo inicial de capacidades.
- Contrato OpenAPI inicial versionado.
- Aplicação Next.js responsiva com apresentação dos três perfis.
- PostgreSQL, Redis e storage S3 compatível (MinIO) para desenvolvimento local.
- Pipeline de CI com lint, testes, builds e validação dos containers.
- Instruções reproduzíveis no README e exemplo de configuração sem segredos.

## Critérios de aceite

- [x] Estrutura do monorepo segue o backlog.
- [x] Comandos de desenvolvimento estão documentados.
- [x] Contrato inicial contém endpoints de saúde e capacidades.
- [x] Erros de validação da API usam o envelope padronizado.
- [x] CI cobre backend, frontend e imagens dos serviços.
- [x] Compose é sintaticamente válido.
- [x] Frontend passa em lint, teste e build local.
- [x] Backend passa em lint e testes localmente via ambiente isolado do `uv`.
- [ ] PR aprovado e staging validado (dependem de repositório remoto e ambiente externo).

## Decisões adiadas deliberadamente

- Retenção de conteúdo e uploads.
- Limites finais de tamanho, duração e tokens.
- Provedor de deploy e configuração de produção.
- Modelo de usuários e ciclo de vida das API Keys.

Esses pontos exigem decisão de produto ou operação e não são necessários para a fundação local.
