# Sprint 8 — Robustez e observabilidade

## Escopo entregue

- Retry exponencial e fallback Gemini → Groq.
- Falha `503` somente depois da indisponibilidade dos dois provedores.
- Worker Celery com estados persistidos e erros sanitizados.
- Falha explícita se a fila Redis não aceitar o job.
- Rate limiting por API Key em janela fixa distribuída no Redis.
- Resposta `429` com `Retry-After` e tempo restante da janela.
- Falha fechada quando o controle de taxa está indisponível.
- Posição real do job entre itens enfileirados/processando.
- Métricas Prometheus de HTTP, latência, jobs e provedores.
- Logs JSON com request ID, rota normalizada, status e duração.
- Alerta estruturado quando headers indicam cota de provedor próxima do limite.
- Validação de assinatura para MP3, WAV, MP4 e MOV.
- Proteção de DOCX contra arquivo inválido, expansão excessiva e razão de compressão suspeita.

## Privacidade dos sinais operacionais

Logs e métricas não incluem prompt, transcrição, nome de arquivo, API Key ou resposta bruta da
LLM. Erros inesperados persistidos no job usam mensagem genérica. Falhas conhecidas incluem
somente código e detalhes operacionais controlados.

## Critérios de aceite

- [x] `429` do Gemini é repetido e pode acionar fallback Groq.
- [x] Falha dos dois provedores produz `503` padronizado.
- [x] Rate limit funciona de forma consistente entre instâncias.
- [x] Usuário enxerga posição na fila sem promessa fictícia de tempo.
- [x] Métricas não expõem request ID nem conteúdo.
- [x] Alertas de cota são gerados a partir de headers reais quando disponíveis.
- [x] Mídia com extensão falsa é rejeitada antes da fila.
- [x] DOCX suspeito é rejeitado antes da análise.
- [ ] Alertas enviados a canal externo (destino de notificação não foi definido).
- [ ] Teste de carga em infraestrutura implantada.

## Decisões ainda necessárias

- Canal de alerta (e-mail, Slack, PagerDuty ou equivalente).
- Política de retenção e exclusão automática.
- Limites de produção após medição de carga real.
