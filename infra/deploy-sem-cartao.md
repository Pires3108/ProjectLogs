# Deploy sem cartão: Firebase + Render + Neon + Upstash

## 1. Preencher as configurações

O arquivo `.env` na raiz já existe e é ignorado pelo Git. Preencha `DATABASE_URL`, `REDIS_URL`,
`GEMINI_API_KEY`, `GROQ_API_KEY`, `API_KEY_PEPPER`, `INTERNAL_TASK_SECRET` e as URLs públicas.
Não faça commit desse arquivo.

Preencha também `frontend/.env.production.local` com a futura URL `onrender.com` da API.

## 2. Banco Neon

Crie um projeto Free, copie a connection string com SSL e troque o prefixo `postgresql://` por
`postgresql+psycopg://`. Localmente, carregue `DATABASE_URL` e execute:

```powershell
Set-Location backend
uv run alembic upgrade head
uv run python -m app.cli create-api-key --name "staging"
```

Guarde a API Key exibida; ela aparece uma única vez.

## 3. API no Render

O Render exige que o código esteja em GitHub/GitLab/Bitbucket. No dashboard, crie um Blueprint a
partir do `render.yaml`, escolha o plano Free e copie os valores secretos do `.env` para as variáveis
marcadas como `sync: false`. O Dockerfile executa as migrações automaticamente antes da API.

Depois do primeiro deploy, copie a URL `https://...onrender.com` para:

- `NEXT_PUBLIC_API_URL` em `frontend/.env.production.local`;
- `CORS_ORIGINS` no Render, usando as duas URLs do Firebase.

## 4. Site no Firebase Hosting

Crie um projeto Firebase no plano Spark, sem ativar Storage, Functions ou App Hosting. Instale ou
execute a CLI sob demanda:

```powershell
npx firebase-tools login
npx firebase-tools use --add
Set-Location frontend
npm ci
npm run build
Set-Location ..
npx firebase-tools deploy --only hosting
```

O build produz `frontend/out`, apontado por `firebase.json`.

## 5. Smoke test

Comece por uma transcrição TXT sintética. Depois valide os três perfis e o download. Áudio/vídeo
dependem da estabilidade do único processo gratuito; mantenha a página aberta para que o polling
continue enquanto o job estiver ativo. Não envie a reunião real sem autorização explícita.
