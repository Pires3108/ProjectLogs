# Sprint 5 — Geração de HTML

## Escopo entregue

- Templates distintos para Estudo, Organização e Backlog.
- Layout responsivo e impressão otimizada.
- CSS integralmente incorporado ao HTML.
- Runtime Mermaid incorporado ao documento, fixado no build do container e sem CDN.
- Diagramas somente quando o toggle está ativo e a análise contém relações explícitas.
- Exemplos, glossário, exercícios, linha do tempo e responsabilidades condicionais.
- Escape automático do conteúdo analisado e sanitização adicional da sintaxe Mermaid.
- Content Security Policy compatível com funcionamento offline.
- Avisos de toggles ignorados incluídos no documento.

## Direção visual

O documento usa a linguagem de um dossiê técnico de reunião: trilho lateral azul-marinho,
marcadores de sinal, tipografia editorial no objetivo e cores específicas por perfil. A
estrutura prioriza leitura, impressão e rastreabilidade em vez de aparência de dashboard.

## Critérios de aceite

- [x] Cada perfil possui estrutura própria.
- [x] Seções desligadas ou sem conteúdo não são renderizadas.
- [x] Fluxos não são inferidos pelo gerador.
- [x] HTML não depende de rede para CSS ou Mermaid.
- [x] Conteúdo não confiável não é executado como HTML ou Mermaid.
- [x] Layout possui adaptação móvel e de impressão.
- [x] Testes cobrem perfis, toggles, ausência de recursos externos e escaping.
- [ ] Inspeção visual em navegador (nenhum navegador controlável estava disponível nesta estação).
- [ ] Screenshot de staging para revisão do PO.

## Artefatos

HTMLs de teste são gerados apenas em memória ou diretórios ignorados. Nenhum documento gerado
nem conteúdo de reunião é versionado.
