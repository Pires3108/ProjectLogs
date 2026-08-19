---
name: ataviva-cli-analyze
description: >-
  Gera um documento AtaViva (perfil Estudo, Organização ou Backlog) a partir de
  uma fonte local, com Claude fazendo a extração da análise diretamente.
  Use quando o usuário pedir para "processar", "gerar documento" ou
  "analisar" uma fonte do AtaViva pela própria conversa.
---

# AtaViva — análise local pela CLI

O AtaViva é hoje só este plugin/CLI: você (Claude) extrai `objetivo`,
`resumo`, `itens`, `decisoes`, `riscos`, `termos_incertos`, `visuais`,
`glossario`, `linha_do_tempo` e `responsabilidades` de uma fonte diretamente
nesta conversa, sem chamar nenhuma API/LLM externa (Gemini, Groq ou outra) —
e depois usa o comando `render-analysis` para gerar o HTML com o motor de
renderização real (templates, CSS, animações) do projeto.

## Passo a passo

1. **Releia as regras de extração antes de começar**, para garantir que estão
   atualizadas (não confie em memória de uma sessão anterior):
   - `backend/app/analysis/prompt.py` — `SYSTEM_INSTRUCTION` e
     `build_analysis_prompt` têm as regras exatas (só usar informação da
     fonte, não inventar responsáveis/prazos/status/complexidade, evidências
     como paráfrases curtas, `objetivo` é um título curto de até ~60
     caracteres, etc.).
   - `backend/app/analysis/models.py` — `StructuredAnalysis` e os modelos
     aninhados (`WorkItem`, `GlossaryTerm`, `TimelineEvent`,
     `ResponsibilityEntry`, `VisualDefinition`) definem o schema exato. Preste
     atenção aos enums: `status` (`concluido`/`em_andamento`/`pendente`/
     `bloqueado`/`incerto`), `complexidade` (`baixa`/`media`/`alta`/
     `incerta`), `tipo` de visual (`fluxograma`/`diagrama`).
   - `backend/app/documents/configuration.py` — `PROFILE_RULES` mostra quais
     toggles cada perfil aceita (`toggles_permitidos`); toggles fora da lista
     do perfil são ignorados com aviso, não gere erro por isso.

2. **Pergunte ou confirme, se ainda não souber**: qual é a fonte (arquivo ou
   texto colado), qual perfil (`estudo`, `organizacao` ou `backlog`) e quais
   toggles habilitar (`fluxogramas`, `diagramas`, `exemplos`, `exercicios`,
   `glossario`, `linha_do_tempo`, `matriz_responsabilidade`).

3. **Leia a fonte** (Read, ou peça o texto direto no chat) e faça a extração
   você mesmo, seguindo as mesmas regras do `SYSTEM_INSTRUCTION`: só use o que
   está na fonte, marque o que não está claro em `termos_incertos`, não
   invente RACI/datas/sequências. Monte o JSON exatamente no formato de
   `StructuredAnalysis` (todos os campos são obrigatórios mesmo que vazios —
   listas vazias `[]`, nunca omita uma chave).

4. **Grave o JSON** em um arquivo temporário (ex.: no diretório de scratch da
   sessão) e valide/gere o HTML com o comando abaixo:

   ```powershell
   cd backend
   .venv/Scripts/python.exe -m app.cli render-analysis `
     --analysis "C:\caminho\analise.json" `
     --perfil estudo `
     --toggles '{"exercicios": true, "glossario": true}' `
     --output "C:\caminho\documento.html"
   ```

   - `--toggles` aceita qualquer subconjunto dos nomes de `ContentToggles`;
     toggles não citados ficam `false`.
   - Se algum toggle for ignorado por não pertencer ao perfil, o comando
     imprime `Aviso: ...` — isso é esperado, não é erro.
   - Se `visuais` estiver preenchido e o toggle `fluxogramas`/`diagramas`
     estiver ativo, o comando precisa de um `mermaid.min.js` real. Se
     `backend/app/static/vendor/mermaid.min.js` não existir localmente (ele só
     é baixado durante o build do Docker), busque um antes:
     `npm install mermaid` em um diretório de scratch e passe
     `--mermaid-asset <caminho para node_modules/mermaid/dist/mermaid.min.js>`.
     Sem isso, o comando falha com `MERMAID_ASSET_UNAVAILABLE` — não é um bug,
     é só o asset vendorizado faltando neste checkout local.
   - **Experimental, atrás de feature flag:** se o usuário quiser que o
     documento siga a identidade visual (cores/fontes, os tokens `--accent`,
     `--spark`, `--ink` etc. definidos em `:root` no `<style>`) de um HTML do
     AtaViva já existente, defina `FEATURE_VISUAL_IDENTITY=true` no `.env` e
     passe `--identidade-visual-documento <caminho.html>` (um arquivo
     específico) ou `--identidade-visual-diretorio <pasta>` (usa o HTML mais
     recente da pasta). Sem a variável de ambiente ligada, os argumentos são
     aceitos mas ignorados com um aviso no console — isso é esperado, é a
     flag desligada, não um bug.

5. **Decida onde salvar o HTML antes de recorrer a `Downloads`.** `Downloads`
   é o último recurso, não o padrão:
   - Se a fonte lida vem de dentro de um projeto/repositório (há um `.git`,
     `README.md`, `package.json` etc. na árvore de pastas acima da fonte),
     procure por uma pasta de documentação já existente nesse projeto —
     `docs/`, `documentation/`, `documentos/` ou `wiki/` (Glob a partir da
     raiz do projeto, 1-2 níveis de profundidade).
   - Se achar uma dessas pastas, salve o HTML lá. Se ela já tiver muitos
     arquivos de tipos variados, crie uma subpasta `ataviva/` dentro dela
     para não misturar; se for uma pasta pequena/dedicada, salve direto nela.
   - Se não achar nenhuma pasta assim, ou não houver um projeto claro por
     trás da fonte, pergunte ao usuário onde salvar ou use `Downloads`.
   - Sempre diga ao usuário onde o arquivo foi salvo e por que escolheu esse
     lugar — nunca decida isso em silêncio.
   - Também pode publicar como Artifact, exceto quando o conteúdo for
     sensível/confidencial (nomes de participantes reais, dados de cliente);
     nesse caso, fica só local, a menos que o usuário peça para publicar.

## O que esta skill não faz

- Não chama nenhuma API/LLM externa (Gemini, Groq) nem depende de banco de
  dados, fila ou serviço web — o projeto agora é só o plugin/CLI local
  (`backend/app/cli.py`). Não há mais site, API nem pipeline em produção para
  substituir.
