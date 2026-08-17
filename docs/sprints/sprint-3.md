# Sprint 3 — Análise estruturada com LLM

## Escopo entregue

- Esquema tipado para objetivo, resumo, itens, decisões, riscos e termos incertos.
- Status, responsáveis, complexidade, evidências e exemplos por item.
- Instruções explícitas para não inventar fatos e sinalizar incerteza.
- Gemini 2.5 Flash como provedor principal com saída JSON estruturada.
- Groq GPT-OSS 120B como fallback com JSON Schema estrito.
- Validação Pydantic adicional, mesmo quando o provedor promete aderência ao esquema.
- Retry com backoff exponencial por provedor.
- Fallback automático após falha ou `429` do Gemini.
- Erro `503` somente depois da falha dos dois provedores.
- Resultado informa provedor, modelo e uso de fallback.

## Critérios de aceite

- [x] A saída cobre os campos exigidos pelo backlog.
- [x] Campos desconhecidos são recusados e todos os campos são obrigatórios no esquema.
- [x] Responsável ausente e complexidade desconhecida não são inventados.
- [x] Gemini é sempre tentado antes do Groq.
- [x] `429`, indisponibilidade e JSON inválido podem acionar retry/fallback.
- [x] Falha de ambos produz o erro padronizado `LLM_PROVIDERS_UNAVAILABLE`.
- [x] Testes HTTP não dependem da rede nem de chaves reais.
- [ ] Análise real em staging (depende das duas API Keys e do ambiente implantado).

## Privacidade

Prompts contêm a fonte da reunião apenas durante a chamada ao provedor. O código não registra
prompt, resposta bruta ou chave. A política de retenção e a autorização para enviar reuniões a
terceiros continuam sendo gates obrigatórios antes do uso com dados de produção.

