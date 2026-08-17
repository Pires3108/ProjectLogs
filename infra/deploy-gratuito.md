# Deploy de staging com custo fixo zero

Esta é a configuração-alvo para o beta. Ela pode permanecer sem custo enquanto o uso ficar nas
franquias gratuitas, mas exige uma conta Google Cloud com faturamento habilitado e contas nos
provedores externos. Configure alertas de orçamento antes de liberar usuários.

## Serviços

- Cloud Run: `ataviva-api`, `ataviva-worker` (privado) e `ataviva-web`.
- Cloud Tasks: fila `ataviva-jobs`, autenticada por OIDC contra o worker.
- Neon: PostgreSQL Free.
- Upstash: Redis Free para rate limit; a fila de jobs é Cloud Tasks.
- Cloudflare R2: bucket privado para fontes e HTMLs.
- Groq: Whisper e fallback de análise; Gemini: análise principal.

## Preparação manual

1. Crie banco Neon, Redis Upstash e bucket R2 na região aprovada para os dados.
2. Aplique `infra/cloudflare/r2-cors.json`, substituindo `FRONTEND_URL`.
3. Crie um projeto GCP, habilite Cloud Run, Cloud Build, Artifact Registry e Cloud Tasks.
4. Crie uma service account para Cloud Tasks com permissão de invocar apenas o worker.
5. Guarde segredos no Secret Manager ou injete-os pelo mecanismo seguro equivalente. Nunca use
   arquivo `.env` em imagem ou repositório.

## Variáveis do backend

Use `JOB_DISPATCHER=cloud_tasks`, `STORAGE_BACKEND=s3`, a URL PostgreSQL com driver
`postgresql+psycopg`, a URL TLS do Redis e os valores `GOOGLE_CLOUD_*`,
`CLOUD_TASKS_WORKER_URL`, `CLOUD_TASKS_SERVICE_ACCOUNT_EMAIL`, `STORAGE_*`, chaves Groq/Gemini,
`API_KEY_PEPPER` e `INTERNAL_TASK_SECRET`. API e worker precisam compartilhar os mesmos segredos.

O serviço público executa o comando padrão da imagem. O worker usa a mesma imagem e permanece
privado; Cloud Tasks chama `POST /internal/jobs/{job_id}/process`. Defina timeout de 30 minutos,
concorrência inicial baixa e máximo de uma instância durante o beta para respeitar cotas gratuitas.

## Build e ordem de publicação

1. Construa e publique `backend/Dockerfile` no Artifact Registry.
2. Execute `alembic upgrade head` como Cloud Run Job ou de uma máquina autorizada.
3. Publique o worker privado e copie sua URL para `CLOUD_TASKS_WORKER_URL`.
4. Crie a fila Cloud Tasks e publique a API pública.
5. Construa `frontend/Dockerfile` com `NEXT_PUBLIC_API_URL` apontando para a API e
   `NEXT_PUBLIC_DIRECT_UPLOAD=true`; publique o site.
6. Atualize `CORS_ORIGINS` na API e o CORS do R2 para a URL final do site.
7. Emita a primeira API Key com `python -m app.cli create-api-key`; entregue-a por canal seguro.

## Smoke test sem conteúdo real

Use fixtures sintéticas para validar os três perfis, cada toggle permitido, upload direto, polling e
download. Só depois das decisões de retenção, região/base legal e acesso ao beta execute o vídeo e a
transcrição reais fornecidos fora do repositório.

## Barreiras para produção

- política de retenção e rotina de exclusão automática;
- provedor de login do site (a API Key atual serve ao beta técnico, não ao público final);
- canal e responsável por alertas;
- aprovação do PO e três exemplos reais, um por perfil;
- teste de carga e regressão visual em navegador disponível.
