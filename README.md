# AtaViva

Gera documentos AtaViva (perfis Estudo, Organização ou Backlog) a partir de
uma fonte de reunião ou documento. Hoje o projeto é só o plugin/CLI: Claude
faz a extração da análise diretamente na conversa (sem chamar Gemini/Groq) e
o comando `render-analysis` gera o HTML final com o motor de renderização do
projeto.

## Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (ou `pip`)

## Uso via skill do Claude Code

A forma recomendada de usar o AtaViva é pela skill
`.claude/skills/ataviva-cli-analyze` — peça a Claude para "processar",
"gerar documento" ou "analisar" uma fonte, e ela cuida da extração e da
chamada do comando abaixo.

## Instalar como plugin do Claude Code

Este repositório é também um marketplace de plugin do Claude Code
(`.claude-plugin/marketplace.json` + `.claude-plugin/plugin.json`), então dá
pra instalar a skill em qualquer sessão sem clonar o repo dentro do projeto
de destino:

```sh
/plugin marketplace add Pires3108/ProjectLogs
/plugin install ataviva@ataviva
```

Também funciona sem registrar marketplace, direto de um clone local ou de
uma URL (sem descoberta via `/plugin`, mas instala igual):

```sh
claude plugin install --plugin-dir /caminho/para/este/repositorio
claude plugin install --plugin-url https://github.com/Pires3108/ProjectLogs/archive/refs/heads/main.zip
```

## Backend (CLI)

```sh
cd backend
uv sync --extra dev
uv run pytest
uv run ruff check .
```

### Gerar um documento a partir de um JSON de análise já pronto

```sh
uv run python -m app.cli render-analysis \
  --analysis analise.json \
  --perfil estudo \
  --toggles '{"exercicios": true, "glossario": true}' \
  --output documento.html
```

`--analysis` é um JSON no formato `StructuredAnalysis`
(`backend/app/analysis/models.py`); `--toggles` aceita qualquer subconjunto
dos nomes de `ContentToggles` (toggles fora dos permitidos pelo perfil são
ignorados com aviso, não erro).

## Segurança de dados

Não adicione uploads, HTMLs gerados, credenciais, conteúdo de reuniões nem
dados pessoais ao repositório. Use apenas fixtures sintéticas nos testes.
