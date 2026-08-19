# AtaViva

Plugin do Claude Code que transforma a transcrição de uma reunião (ou
qualquer documento-fonte) em um documento HTML pronto para consulta, em um
de três formatos: **Estudo** (material didático), **Organização** (decisões
e ações) ou **Backlog** (o que foi feito / o que falta).

Hoje o projeto é só isso — plugin + CLI local. Não há site, API, banco de
dados nem chamada a LLM externa (Gemini/Groq): quem lê a fonte e extrai os
fatos é o próprio Claude, dentro da conversa; o código em `backend/` só
valida esse JSON e renderiza o HTML final.

## Instalação

Requer o [Claude Code](https://claude.ai/code) instalado.

**Opção recomendada — via marketplace:**

```sh
/plugin marketplace add Pires3108/ProjectLogs
/plugin install ataviva@ataviva
```

**Sem registrar marketplace** (clone local ou URL de um zip do repo):

```sh
claude plugin install --plugin-dir /caminho/para/este/repositorio
claude plugin install --plugin-url https://github.com/Pires3108/ProjectLogs/archive/refs/heads/main.zip
```

Qualquer uma das três formas instala a skill `ataviva-cli-analyze`, que fica
disponível em qualquer sessão do Claude Code (não precisa clonar o repo
dentro do projeto onde você vai usar o AtaViva).

Se preferir só rodar o CLI direto (sem o plugin), veja [Backend (CLI)](#backend-cli)
abaixo — mas nesse caso a extração da análise fica por sua conta.

## Como usar

Basta pedir a Claude para **"processar"**, **"gerar documento"** ou
**"analisar"** uma fonte (arquivo ou texto colado no chat). A skill então:

1. **Confirma com você**, se ainda não souber: qual a fonte, qual perfil
   (Estudo/Organização/Backlog) e quais seções extras habilitar (toggles).
2. **Pergunta o nível de profundidade** da extração, se você não tiver
   indicado um (veja tabela abaixo).
3. **Lê a fonte e extrai os fatos** ela mesma — objetivo, resumo, itens de
   trabalho, decisões, riscos, termos incertos, glossário, linha do tempo,
   responsabilidades e diagramas — sem inventar dado que não está na fonte.
4. **Roda o CLI** (`render-analysis`) para gerar o HTML final.
5. **Salva o arquivo** em uma pasta de documentação do projeto de destino
   (`docs/`, `documentos/` etc.), se encontrar uma, ou pergunta onde salvar.

### Perfis de documento

| Perfil | Foco | Seções extras disponíveis |
|---|---|---|
| `estudo` | Explicar o conteúdo para aprendizado | fluxogramas, diagramas, exemplos, exercícios (quiz), glossário |
| `organizacao` | Decisões, ações e prazos | fluxogramas, diagramas, exemplos, linha do tempo, matriz de responsabilidade |
| `backlog` | O que foi concluído / o que falta | fluxogramas, diagramas, exemplos, matriz de responsabilidade |

Um toggle pedido fora da lista do perfil escolhido é simplesmente ignorado
(com aviso), não gera erro.

### Nível de profundidade

Controla o quanto a extração se aprofunda na fonte — quanto mais profundo,
mais tokens a conversa consome e maior/mais detalhado sai o documento:

| Nível | O que muda |
|---|---|
| **Raso** | Só o essencial: itens/decisões/riscos principais, descrições de 1 frase, no máx. 1 evidência por item |
| **Médio** *(padrão)* | Cobertura equilibrada de tudo que foi claramente discutido na fonte |
| **Profundo** | Cobertura abrangente, inclui pontos secundários, descrições e evidências mais completas |
| **Estendido** | Extração exaustiva — nada é descartado, glossário/linha do tempo no maior detalhe possível |

Isso nunca afeta as regras fixas de extração (não inventar responsável,
prazo, status ou complexidade; `objetivo` continua um título curto) — só
controla a quantidade e o detalhe do que é extraído.

## Backend (CLI)

Para desenvolver ou rodar o CLI diretamente (fora do fluxo da skill):

```sh
cd backend
uv sync --extra dev      # instala dependências
uv run pytest            # roda os testes
uv run ruff check .      # lint (mesmo gate do CI)
```

### `render-analysis`

Recebe um JSON já pronto no formato `StructuredAnalysis` (é isso que a
skill produz no passo 3 acima) e gera o HTML:

```sh
uv run python -m app.cli render-analysis \
  --analysis analise.json \
  --perfil estudo \
  --toggles '{"exercicios": true, "glossario": true}' \
  --output documento.html
```

| Flag | Obrigatória | O que faz |
|---|---|---|
| `--analysis` | sim | Caminho do JSON no formato `StructuredAnalysis` (`backend/app/analysis/models.py`) |
| `--perfil` | sim | `estudo`, `organizacao` ou `backlog` |
| `--toggles` | não | JSON com os toggles a habilitar; qualquer nome de `ContentToggles` fora do permitido pelo perfil é desativado com um aviso impresso no console, não um erro |
| `--output` | sim | Caminho do arquivo HTML de saída |
| `--mermaid-asset` | não | Caminho alternativo para `mermaid.min.js`, usado quando `visuais` tem fluxogramas/diagramas habilitados. Sem esse asset (ele não vem versionado no checkout local, só é baixado no build Docker) o comando falha com `MERMAID_ASSET_UNAVAILABLE` |
| `--identidade-visual-documento` | não | **Experimental**, requer `FEATURE_VISUAL_IDENTITY=true` no `.env`. Reaplica a identidade visual (cores/fontes) de um HTML do AtaViva já existente |
| `--identidade-visual-diretorio` | não | Mesma ideia, mas aponta para uma pasta — usa o HTML mais recente dela. Mutuamente exclusiva com a flag acima |

Com a feature flag desligada, as duas flags de identidade visual são aceitas
mas ignoradas (aviso no console) — comportamento esperado de uma flag
experimental desligada, não um bug.

## Segurança de dados

Não adicione uploads, HTMLs gerados, credenciais, conteúdo de reuniões nem
dados pessoais ao repositório. Use apenas fixtures sintéticas nos testes
(`backend/tests/analysis_fixtures.py`).
