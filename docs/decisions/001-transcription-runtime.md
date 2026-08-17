# ADR 001 — Runtime de transcrição

- Status: decidido — API Groq no protótipo implantado
- Contexto: Sprint 2

## Problema

O backlog define Whisper, mas deixa aberta a execução self-hosted ou por API. A escolha afeta
privacidade, infraestrutura, latência, limites, custo e tratamento de falhas.

## Opções

### A. `faster-whisper` local

- Conteúdo permanece na infraestrutura controlada pelo projeto.
- Não há custo variável por chamada.
- Requer CPU/GPU, download de modelos e planejamento de capacidade.

### B. API externa

- Operação e escalabilidade iniciais mais simples.
- Conteúdo é enviado a terceiro e fica sujeito a cota, preço e disponibilidade.

### C. Híbrida

- Permite fallback e escolha por ambiente.
- Aumenta a complexidade operacional e de testes.

## Estado implementado

O domínio depende apenas de `TranscriptionProvider`. Arquivos são resolvidos por IDs opacos,
resultados têm texto, idioma, duração, segmentos, provedor e modelo, e falhas são convertidas
para o contrato público sem incluir o conteúdo da reunião. Nenhuma opção foi escolhida
implicitamente.

## Decisão

Usar Groq com `whisper-large-v3-turbo` como primeira implementação, porque possui camada
gratuita, aceita português e evita a necessidade de GPU no deploy inicial. O adaptador local
continua possível pelo contrato `TranscriptionProvider`.

Como o free tier aceita arquivos de até 25 MB, o backend extrai a primeira faixa de áudio com
FFmpeg, converte para mono/16 kHz/32 kbps e divide em blocos de 20 minutos. Os blocos são
enviados sequencialmente e seus timestamps são recompostos no resultado.

Esta escolha não representa garantia de operação gratuita em produção. Ao atingir a cota, o
job deve aguardar ou falhar de forma explícita; ativar cobrança exigirá decisão separada.
