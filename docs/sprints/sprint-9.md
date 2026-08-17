# Sprint 9 — Beta

Status: preparação técnica concluída; validação com usuários reais bloqueada por decisões externas.

## Entregue

- arquitetura de staging sem custo fixo e runbook de publicação;
- Cloud Tasks para execução assíncrona sem worker permanente;
- armazenamento S3/R2 para fontes e HTMLs;
- upload direto com URL pré-assinada para vídeos acima do limite do Cloud Run;
- ticket temporário assinado, vinculado à API Key, nome e tamanho esperado;
- frontend alterna para upload direto em staging;
- contrato OpenAPI e testes automatizados atualizados.
- JSON estruturado persistido e devolvido junto ao link do HTML;
- limite configurável de três horas e estimativa de espera da fila;
- visualização do HTML pelo site e comando seguro para aplicar futura política de retenção.

## Evidência local

- export Read.AI real reconhecido estruturalmente sem persistir conteúdo no repositório;
- vídeo real tem aproximadamente 206 MB e cabe no limite de 500 MB da aplicação;
- backend e frontend passam em testes, lint e build;
- Docker Compose é sintaticamente válido.

## Pendências que não podem ser inferidas

- política e prazo de retenção de fontes, resultados e uploads abandonados;
- região e base legal aprovadas para conteúdo real;
- provedor de login e modelo de acesso do site final;
- canal/responsável por alertas operacionais;
- credenciais e autorização para criar recursos externos;
- aprovação do PO e seleção de exemplos reais para cada perfil;
- navegador disponível para regressão visual e usuários do beta.

A auditoria detalhada e a distinção entre evidência local e gates externos estão em
`docs/beta-readiness.md`.
