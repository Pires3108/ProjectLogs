# Sprint 6 — API pública e autenticação

## Escopo entregue

- PostgreSQL em produção e SQLite para desenvolvimento/testes.
- Migração Alembic inicial para API Keys, jobs e fontes.
- API Keys aleatórias com prefixo identificável e HMAC-SHA256 com pepper.
- Expiração, revogação e registro do último uso.
- Chave bruta exibida somente no momento da emissão pelo CLI.
- Criação multipart de jobs com perfil, toggles e múltiplas fontes.
- Persistência de configuração efetiva, avisos, fontes e texto normalizado.
- Consulta de status e download autenticado do HTML quando pronto.
- Isolamento por API Key, retornando `404` para jobs de outro cliente.
- Estados `queued`, `processing`, `done` e `failed`.
- Contrato OpenAPI com esquema de segurança `X-API-Key`.

## Critérios de aceite

- [x] API Key ausente, inválida, revogada ou expirada retorna `401` padronizado.
- [x] Nenhuma chave bruta é persistida.
- [x] Jobs começam em `queued` e preservam perfil/toggles normalizados.
- [x] Mais de uma fonte pode ser associada ao mesmo job.
- [x] Acesso cruzado entre chaves é impedido sem revelar existência do job.
- [x] Download antes da conclusão retorna `409 JOB_NOT_READY`.
- [x] Migração cria todas as tabelas e não diverge dos modelos ORM.
- [x] OpenAPI documenta autenticação, entrada e respostas.
- [ ] Revogação por painel administrativo (não há painel administrativo no escopo definido).

## Retenção

Não foi criado prazo automático de exclusão porque o backlog o deixa explicitamente a definir.
Até a decisão de produto, a remoção é operacional e nenhuma alegação de retenção limitada deve
ser feita em produção.
