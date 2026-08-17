# Matriz de prontidão do beta

Auditoria em 2026-08-17 contra `backlog-projeto.md`.

## Com evidência automatizada

- ingestão de múltiplas fontes e limites por categoria;
- normalização de TXT/Read.AI, VTT, SRT, Markdown e DOCX;
- áudio/vídeo com validação de assinatura, limite de 3 horas, conversão e divisão em chunks;
- Gemini principal, Groq fallback, retry exponencial, saída estruturada e erro 503 consolidado;
- três perfis, regras de toggles e avisos para combinações ignoradas;
- HTML autocontido, responsivo, escapado e Mermaid apenas quando aplicável;
- API Key com HMAC, expiração, revogação, ownership e rate limit;
- jobs assíncronos, posição e estimativa da fila, JSON da análise e HTML;
- upload direto R2/S3 com ticket temporário, confirmação de tamanho e uso único;
- métricas Prometheus, logs estruturados sem corpo e avisos de cota;
- frontend com upload, configuração, histórico de sessão, polling, visualização e download;
- migrações Alembic, contrato OpenAPI, lint, testes e build em CI.
- comando de limpeza com corte explícito, simulação por padrão e exclusão coordenada de fontes,
  HTML e metadados; o agendamento aguarda a política de retenção.

## Evidência dos arquivos reais fornecidos

- transcrição Read.AI: 33.314 bytes, 85 falas reconhecidas, 31.443 caracteres normalizados e
  último timestamp em 2.275 segundos;
- vídeo: aproximadamente 206 MB, abaixo do limite configurado de 500 MB;
- nenhum conteúdo foi copiado para fixture, log ou repositório e nenhuma fonte foi enviada a
  provedor externo.

## Sem evidência suficiente / requer ação externa

- staging publicado e smoke test real nos três perfis;
- transcrição real pelo Groq e análise real Gemini/Groq, que exigem chaves e autorização para
  compartilhar conteúdo da reunião;
- login do site, cuja identidade/provedor ainda não foi definido;
- retenção e exclusão automática, pois o prazo e o tratamento de uploads abandonados não foram
  definidos;
- alertas externos, pois faltam canal, destinatários e ferramenta;
- teste de carga sob cotas reais dos provedores;
- regressão visual em navegador (o navegador integrado não estava disponível);
- usuários reais, aprovação do PO e revisão/PR.

Os itens desta última seção são gates da Definition of Done e não podem ser declarados concluídos
com testes locais ou escolhas presumidas.
