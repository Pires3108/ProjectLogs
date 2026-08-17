# ADR 003 — Arquitetura de deploy sem custo fixo inicial

- Status: proposta adotada para o protótipo
- Revisar antes de produção comercial

## Componentes

- Frontend e backend: containers no Google Cloud Run, escalando a zero.
- Execução assíncrona: Cloud Tasks aciona um segundo serviço Cloud Run privado; não há worker
  permanentemente ligado.
- PostgreSQL: Neon Free durante protótipo.
- Fila/controle de taxa: Upstash Redis Free.
- Uploads e HTMLs: Cloudflare R2 Standard dentro da franquia gratuita.
- Transcrição: Groq Whisper free tier.
- Análise: Gemini free tier com fallback Groq, conforme backlog.

## Motivos

O Cloud Run executa containers e possui franquia mensal, evitando adaptar FastAPI ou Next.js a
um runtime proprietário. O limite de 32 MiB para requisições HTTP/1 impede enviar vídeos grandes
através da API implantada; o frontend usa upload direto por URL pré-assinada do R2. O
arquivo de exemplo tem aproximadamente 206 MB e confirma que essa arquitetura é necessária.

O upload direto usa tickets HMAC temporários, vinculados à API Key e ao tamanho esperado. O job
só é criado depois que o backend confirma a presença e o tamanho do objeto.

## Limites

"Gratuito" significa operar dentro das franquias atuais, sem SLA. Cotas podem mudar e serviços
podem pausar. Antes de dados reais em produção, devem ser aprovadas retenção, região, termos dos
provedores, base legal e orçamento para excedentes. Nenhuma cobrança automática será ativada
por esta decisão.
