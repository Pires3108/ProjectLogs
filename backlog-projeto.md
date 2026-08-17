# Backlog do Projeto — Documentação Automática de Reuniões

> **Nome sugerido (placeholder):** *AtaViva*
> Ajuste o nome, mas o restante do documento não depende dele.

**Changelog desta versão:** motor de análise trocado para LLM gratuita (com fallback), suporte a upload de documentos (.md, .docx e extensível a outros formatos), seleção de **perfil de documento** (estudo / organização / backlog) e **toggles** configuráveis de conteúdo (fluxogramas, diagramas, exercícios, etc.).

---

## Visão geral do fluxo

```
┌─────────────────────┐
│       FONTES          │  Read.AI · Áudio · Vídeo · Transcrição (.txt/.vtt/.srt)
│  (1 ou mais por        │  Documento (.md, .docx, extensível a .pdf/.odt/...)
│   análise)              │
└──────────┬───────────┘
           ▼
┌─────────────────────┐
│  INGESTÃO/FILA + NORM. │  Upload → validação → normalização de documentos
│  (converte tudo p/ texto)│ (md/docx/etc. → texto puro) → fila assíncrona
└──────────┬───────────┘
           ▼
┌─────────────────────┐
│    TRANSCRIÇÃO         │  Só roda se a fonte for áudio/vídeo sem transcrição
│    (se necessário)       │
└──────────┬───────────┘
           ▼
┌─────────────────────┐
│  ANÁLISE COM LLM        │  LLM gratuita (motor principal + fallback)
│  GRATUITA                │  Extrai: objetivo, status, responsáveis, complexidade, exemplos
└──────────┬───────────┘
           ▼
┌─────────────────────┐
│  PERFIL & TOGGLES       │  Usuário escolhe: Estudo / Organização / Backlog
│  (config. de saída)      │  + liga/desliga: fluxogramas, diagramas, exercícios, etc.
└──────────┬───────────┘
           ▼
┌─────────────────────┐
│  GERADOR DE SAÍDA       │  → HTML (template por perfil, seções condicionais)
│                           │  → Resposta da API (JSON estruturado + link do HTML)
└─────────────────────┘
```

---

## 1. Objetivo

Automatizar a criação de documentação a partir de múltiplas fontes de uma reunião (export do Read.AI, áudio, vídeo, transcrição de texto **ou documento já escrito** em `.md`/`.docx`/formatos similares), usando uma **LLM gratuita** para a análise, e gerar um **HTML explicativo e navegável** cujo conteúdo e formato se adaptam ao que o usuário precisa — **estudo, organização ou backlog de projeto** — com elementos visuais (diagramas, fluxogramas, exercícios etc.) que podem ser **ativados ou desativados** conforme a necessidade. Tudo isso disponível tanto por um **site** quanto por uma **API autenticada por chave**.

---

## 2. Resultado esperado

- Site funcional onde o usuário envia **uma ou mais fontes** por análise: Read.AI, áudio, vídeo, transcrição **ou documento** (`.md`, `.docx`, com arquitetura pronta para aceitar outros formatos como `.pdf`/`.odt`/`.rtf` no futuro).
- Antes de gerar o documento, o usuário escolhe:
  1. **Perfil do documento** — `Estudo`, `Organização` ou `Backlog do projeto` (cada um com estrutura e tom de escrita diferentes);
  2. **Toggles de conteúdo** — liga/desliga por seção, ex.: fluxogramas, diagramas, exemplos, glossário, exercícios (só disponível no perfil Estudo), linha do tempo, matriz de responsabilidades (RACI).
- Motor de análise rodando em **LLM gratuita**, com estratégia de fallback entre provedores para não depender de um único free tier.
- **HTML final** gerado de acordo com o perfil e os toggles escolhidos.
- **API REST documentada** (OpenAPI/Swagger), autenticada por **API Key**, aceitando os mesmos parâmetros (fontes + perfil + toggles) que o site.
- Painel simples de acompanhamento do status de processamento (fila, pronto, erro).

### Perfis de documento (estrutura de cada um)

| Perfil | Foco | Seções típicas |
|---|---|---|
| **Estudo** | Explicar o conteúdo p/ aprendizado | Resumo do tema, conceitos-chave, glossário, **exercícios**, sugestões de aprofundamento |
| **Organização** | Estruturar o que foi discutido | Decisões tomadas, ações e prazos, linha do tempo, matriz de responsabilidades |
| **Backlog do projeto** | Rastrear execução do projeto | O que já foi feito, o que falta, responsável por parte, nível de complexidade, exemplos |

### Toggles de conteúdo (exemplo de configuração via API)

```json
{
  "perfil": "estudo",
  "toggles": {
    "fluxogramas": true,
    "diagramas": true,
    "exemplos": true,
    "exercicios": true,
    "glossario": true,
    "linha_do_tempo": false,
    "matriz_responsabilidade": false
  }
}
```
> Regra de validação: toggles que não fazem sentido fora do seu perfil (ex.: `exercicios` fora de `estudo`) são ignorados/desativados automaticamente pelo backend, com aviso no retorno — não é erro fatal, mas também não é uma combinação livre sem regras.

---

## 3. Arquitetura, formatação e stack

**Componentes principais**
| Componente | Função |
|---|---|
| Frontend (site) | Upload multi-fonte, seleção de perfil/toggles, acompanhamento de status, visualização/download do HTML |
| API Gateway / Backend | Recebe requisições (site e API externa), orquestra o pipeline |
| Fila assíncrona | Processa arquivos grandes (áudio/vídeo) sem travar a requisição |
| **Normalizador de documentos** | Converte `.md`, `.docx` (e formatos futuros) em texto puro/estruturado antes da análise |
| Serviço de transcrição | Converte áudio/vídeo em texto quando não há transcrição pronta |
| **Serviço de análise (LLM gratuita)** | Extrai objetivo, status, responsáveis, complexidade, exemplos — com fallback entre provedores |
| Gerador de HTML | Monta o HTML final a partir do template do perfil escolhido, com diagramas via Mermaid.js (só quando o toggle está ativo) |
| Storage de arquivos | Guarda uploads e HTMLs gerados (bucket S3-compatível) |
| Banco de dados | Jobs, usuários, API Keys, metadados das análises, perfis/toggles usados |
| Autenticação | Login (site) e API Key (uso programático) |
| Observabilidade | Logs estruturados, métricas, alertas |

### Escolha da LLM gratuita (pesquisa)

Como as reuniões podem gerar transcrições longas (facilmente 10–30 mil tokens em 1–2h), o critério principal foi **janela de contexto grande + cota gratuita viável para produção**, não só "ser de graça":

| Opção | Tipo | Pontos fortes | Limite do free tier (pode mudar) | Papel no projeto |
|---|---|---|---|---|
| **Google Gemini API — Flash / Flash-Lite** ✅ escolha principal | Free tier oficial da Google | Contexto de até 1M tokens (cabe a reunião inteira sem dividir em pedaços), suporta saída estruturada (JSON) nativamente | ~10–15 requisições/min, até ~1.000–1.500 requisições/dia dependendo do modelo | Motor principal de análise |
| **Groq — Llama 3.3 70B / GPT-OSS-120B** ✅ fallback | Free tier de inferência para modelos open-source | Extremamente rápido (300–800 tokens/s), API compatível com o formato OpenAI (troca simples) | ~30 req/min, ~14.400 req/dia, mas com limite de tokens/min mais apertado | Fallback automático se o Gemini estourar cota ou falhar |
| Llama 3 / Qwen3 / Mistral via Ollama (self-hosted) | Open-source, gratuito se você tem a máquina | Sem limite de cota de terceiros, mais privacidade | Exige GPU própria (custo de infraestrutura, não de licença) | Alternativa para quem quiser rodar 100% local, sem depender de provedor externo |

**Decisão:** usar **Gemini (Flash/Flash-Lite) como motor principal**, por causa da janela de contexto grande (evita ter que cortar a transcrição em pedaços) e cota diária suficiente para o volume esperado; com **Groq como fallback automático** em caso de erro `429` (limite excedido) ou indisponibilidade. O acesso aos dois é feito por uma camada de abstração única no backend (ex.: client próprio ou lib tipo LiteLLM), para trocar de provedor sem reescrever o pipeline de análise — importante porque limites de free tier mudam com frequência.

> ⚠️ Ponto de atenção arquitetural: como o motor de análise depende de cotas gratuitas, **a capacidade de processamento do sistema fica limitada pela cota do provedor**, não só pela sua própria infraestrutura. Isso precisa entrar no dimensionamento (fila com controle de taxa, fila de espera visível ao usuário) — ver seção 4.

### Normalização de documentos e formatação do HTML
- Camada de normalização usando um conversor universal (ex.: Pandoc ou biblioteca equivalente) para `.md`, `.docx` → texto estruturado; arquitetura pronta para adicionar `.pdf`/`.odt`/`.rtf` depois, sem mudar o pipeline de análise.
- Template do HTML varia por **perfil** (Estudo/Organização/Backlog), com seções renderizadas condicionalmente conforme os **toggles**.
- Diagramas/fluxogramas via Mermaid.js embutido, gerados apenas quando o toggle correspondente está ativo **e** o conteúdo realmente tiver um fluxo/processo (não forçar diagrama vazio).
- CSS embutido no próprio HTML (autocontido, funciona offline), responsivo.

**Stack sugerida** (ajustável):
- **Frontend:** React + Next.js + TailwindCSS
- **Backend:** Python + FastAPI
- **Fila:** Redis + Celery
- **Transcrição:** Whisper (self-hosted ou via API)
- **Normalização de documentos:** Pandoc (ou `python-docx` + `markdown-it` como alternativa mais leve)
- **Análise:** Gemini API (free tier) como principal, Groq (free tier) como fallback, via camada de abstração
- **Banco:** PostgreSQL
- **Storage:** S3 ou compatível (ex.: Cloudflare R2)
- **Infra:** Docker, CI/CD (GitHub Actions), deploy em nuvem

---

## 4. Responsabilidades e limites

**O sistema faz:**
- Aceita e combina mais de uma fonte na mesma análise, incluindo documentos já escritos.
- Adapta o conteúdo gerado ao perfil e aos toggles escolhidos pelo usuário.
- Gera HTML e disponibiliza link/download; expõe API equivalente.

**O sistema não faz:**
- Não grava nem gerencia reuniões (não substitui Read.AI/Zoom/Meet).
- Não altera os arquivos originais enviados.
- Não garante 100% de precisão na atribuição de responsáveis ou na geração de exercícios — depende da qualidade da fonte e da LLM gratuita usada.
- Não guarda dados além do necessário para o processamento (retenção a definir).

**Limites técnicos (parametrizáveis):**
- Formatos aceitos v1: Read.AI (export), `.mp3/.wav/.mp4/.mov`, `.txt/.vtt/.srt`, `.md/.docx` — outros formatos entram sob demanda.
- Tamanho máximo de arquivo (ex.: 500 MB vídeo, 200 MB áudio, 20 MB documento).
- Duração máxima de reunião (ex.: 3h) / tamanho máximo de transcrição em tokens (para caber no contexto da LLM escolhida).
- Idiomas suportados inicialmente (ex.: PT-BR e EN).
- **Rate limit efetivo = o menor entre o limite da sua API e a cota livre do provedor de LLM ativo no momento** — isso deve ser exposto ao usuário (ex.: "fila estimada: X min") em vez de só falhar silenciosamente.
- Toggles fora de contexto do perfil (ex. `exercicios` em `backlog`) são ignorados, não geram erro.

**Papéis sugeridos da equipe:**
- **PO:** prioriza backlog e valida entregas.
- **Backend:** pipeline de ingestão/normalização, fila, integração com LLM (+fallback), API.
- **Frontend:** site de upload, seleção de perfil/toggles, visualização.
- **DevOps:** infraestrutura, CI/CD, monitoramento (inclusive de cota de LLM).
- **QA:** testes e validação da qualidade dos HTMLs gerados por perfil.

---

## 5. Tratamento e padronização de erros

- **Formato padrão de erro (JSON):**
  ```json
  { "error": { "code": "STRING", "message": "STRING", "details": {}, "request_id": "STRING" } }
  ```
- **Categorias:**
  - `400` — validação (formato não suportado, arquivo corrompido, perfil inexistente)
  - `401/403` — API Key ausente, inválida ou expirada
  - `413` — arquivo acima do limite
  - `422` — conteúdo insuficiente para gerar análise, ou combinação perfil+toggle inválida (quando bloqueante)
  - `429` — limite de requisições excedido (do próprio serviço)
  - `500` — erro interno
  - `503` — **ambos** os provedores de LLM gratuitos indisponíveis/sem cota (principal + fallback)
- **Jobs assíncronos** com status consultável: `queued` → `processing` → `done` / `failed` (com motivo do erro, incluindo qual provedor de LLM foi usado).
- **Retry/fallback:** em falha ou `429` do provedor principal (Gemini), tenta automaticamente o fallback (Groq) antes de marcar o job como falho; backoff exponencial entre tentativas.
- **Logs:** estruturados, com `request_id`/`correlation_id` e qual provedor/perfil/toggles foram usados; sem dado sensível (PII) em texto puro.
- **Alertas:** cota de LLM próxima do limite ou falhas recorrentes geram notificação.

---

## 6. Testes

- **Unitários:** parser de cada tipo de fonte (incluindo `.md`/`.docx`), normalizador de documentos, geração de cada bloco do HTML por perfil.
- **Integração:** pipeline completo (fonte → análise → HTML final) com mocks do Gemini/Groq.
- **Fallback de LLM:** simular falha/429 do provedor principal e validar troca automática para o fallback.
- **Perfis e toggles:** testar as combinações relevantes (cada perfil × toggles válidos) e a regra de ignorar toggles fora de contexto.
- **Contrato de API:** validação automática contra a especificação OpenAPI.
- **Ponta a ponta (E2E):** upload real (cada tipo de fonte) → processamento → download, pelo site e pela API.
- **Carga/performance:** arquivos grandes e múltiplos jobs simultâneos, respeitando a cota do provedor de LLM ativo.
- **Regressão visual:** conferir renderização de diagramas/fluxogramas quando os toggles estão ativos e a ausência deles quando desativados.
- **Segurança:** API Key inválida/revogada, rate limiting, upload de arquivo malicioso.

---

## 7. Sprints definidas (sugestão, ciclos de 2 semanas)

| Sprint | Foco |
|---|---|
| 0 | Fundação: repositório, CI/CD, infra básica, contrato inicial da API (OpenAPI) |
| 1 | Ingestão multi-fonte: upload de áudio/vídeo/transcrição **+ documentos (.md/.docx)** e normalização |
| 2 | Transcrição: integração do serviço de transcrição + parser do export do Read.AI |
| 3 | Integração da **LLM gratuita** (Gemini principal + Groq fallback) e extração estruturada |
| 4 | **Perfis de documento e toggles**: modelagem de dados, validação de combinações, templates por perfil |
| 5 | Geração de HTML: diagramas/fluxogramas condicionais (Mermaid), layout responsivo por perfil |
| 6 | API pública: autenticação por API Key, endpoints (incluindo perfil/toggles), documentação (Swagger/Redoc) |
| 7 | Frontend/site: upload multi-formato, seleção de perfil/toggles, histórico, visualização/download |
| 8 | Robustez: fallback de LLM, tratamento de erros, rate limiting, monitoramento de cota |
| 9 | Beta: testes com usuários reais, ajustes finais, documentação |

---

## 8. Definition of Done

Uma entrega é considerada concluída quando:
- [ ] Código revisado (PR aprovado) e sem pendência de lint/build.
- [ ] Testes unitários e de integração passando, incluindo os cenários de fallback de LLM e de perfil/toggles.
- [ ] Endpoint novo/alterado documentado na especificação OpenAPI.
- [ ] Erros tratados conforme o padrão definido na seção 5.
- [ ] Feature validada em ambiente de staging com pelo menos um exemplo real por perfil (Estudo/Organização/Backlog).
- [ ] Critérios de aceite da sprint revisados e aprovados pelo PO.
- [ ] Sem regressão nos testes E2E principais.
- [ ] Documentação (README/wiki) atualizada quando aplicável.
