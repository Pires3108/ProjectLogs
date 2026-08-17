# ADR 004 — Staging sem cartão

- Status: adotada para o beta de baixo volume
- Substitui o ADR 003 como caminho prioritário de staging

## Decisão

- site estático no Firebase Hosting, plano Spark;
- API FastAPI em um Render Free Web Service;
- PostgreSQL no Neon Free;
- Redis TLS no Upstash Free para rate limit;
- Gemini e Groq nos respectivos free tiers;
- uploads no disco efêmero do Render apenas durante o processamento;
- análise e HTML final persistidos no Neon;
- fila best-effort em uma única thread dentro do processo do Render.

## Por que não Firebase ou Hugging Face para todo o sistema

Em 2026, Cloud Storage for Firebase exige Blaze e conta de faturamento. Cloud Functions, Cloud Run
e integrações dinâmicas do Hosting também exigem billing. Portanto, somente o Hosting estático cabe
no requisito sem cartão.

Novos Docker/Gradio Spaces da Hugging Face exigem plano pago; apenas Static Spaces e casos
específicos de ZeroGPU continuam disponíveis gratuitamente. Um Static Space não executa FastAPI,
FFmpeg ou o pipeline assíncrono.

## Limitações aceitas no beta

- Render pode pedir cartão para verificação de conta, embora o serviço Free funcione sem método de
  pagamento em contas aceitas;
- a API hiberna após 15 minutos sem tráfego e pode levar cerca de um minuto para acordar;
- o filesystem é efêmero e o serviço pode reiniciar, fazendo um job em andamento falhar;
- a fila está dentro do processo, sem garantia de entrega;
- polling do frontend mantém tráfego durante um job, mas não elimina reinícios da plataforma;
- não é uma arquitetura de produção nem possui SLA.

Se o Render exigir cartão para esta conta, não há substituto equivalente que execute o container
FastAPI + FFmpeg de forma confiável e irrestrita. A alternativa seria reescrever o backend para
Workers/Edge e mover a extração de áudio para o navegador, o que é uma mudança arquitetural grande.
