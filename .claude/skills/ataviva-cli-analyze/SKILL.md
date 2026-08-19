---
name: ataviva-cli-analyze
description: >-
  Gera um documento AtaViva (perfil Estudo, Organização ou Backlog) a partir de
  uma fonte local, com Claude fazendo a extração da análise diretamente —
  sem chamar Gemini ou Groq. Use quando o usuário pedir para "processar",
  "gerar documento" ou "analisar" uma fonte do AtaViva pela própria conversa,
  localmente, em vez de usar a API/site.
---

# AtaViva — análise local pela CLI

Este projeto (AtaViva) normalmente extrai `objetivo`, `resumo`, `itens`,
`decisoes`, `riscos`, `termos_incertos`, `visuais`, `glossario`,
`linha_do_tempo` e `responsabilidades` de uma fonte chamando Gemini (e Groq
como fallback) por HTTP. Esta skill existe para fazer esse mesmo trabalho
**localmente, com você (Claude) fazendo a extração**, sem tocar em nenhum
provedor externo — útil quando os provedores estão indisponíveis, com quota
esgotada, ou quando o usuário só quer testar/gerar um documento rapidamente
nesta conversa.

O motor de renderização (templates, CSS, animações) é o mesmo usado em
produção — só a etapa de "chamar um LLM por HTTP" é substituída por você
mesmo fazendo a extração.

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
   sessão) e valide/gere o HTML com o comando abaixo — ele reusa o gerador
   real, então o resultado é idêntico ao que a API geraria:

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

- Não cria, atualiza nem consulta jobs no banco de dados do AtaViva — é um
  caminho totalmente paralelo ao pipeline real (API → Celery → Gemini/Groq).
  Nenhum job fica registrado, nenhuma chave de API é consumida.
- Não substitui o pipeline em produção (Render). Para isso, veja a opção de
  adicionar um provedor de análise de verdade em
  `backend/app/analysis/factory.py` — assunto separado, não coberto aqui.
