# Sprint 7 — Frontend operacional

## Escopo entregue

- Upload de múltiplas fontes com formatos v1 filtrados no seletor.
- Lista de arquivos e tamanhos antes do envio.
- Perfis carregados do catálogo real da API.
- Toggles habilitados/desabilitados conforme o perfil escolhido.
- Criação multipart de job autenticado.
- Polling de estados `queued` e `processing` a cada dois segundos.
- Apresentação de avisos e falha do job.
- Download autenticado do HTML pronto.
- Histórico dos oito jobs recentes apenas durante a sessão do navegador.
- API Key mantida somente em memória, sem localStorage ou sessionStorage.
- Layout responsivo, foco visível e respeito a movimento reduzido.

## Direção visual

A interface funciona como uma mesa de documentação técnica, com trilho de processo, tipografia
editorial e painéis de entrada. A hierarquia acompanha as três etapas reais: entrada,
processamento e histórico da sessão.

## Critérios de aceite

- [x] Usuário seleciona múltiplos formatos e vê os arquivos escolhidos.
- [x] Perfis e toggles permanecem sincronizados com o backend.
- [x] Job é criado e acompanhado até estado terminal.
- [x] HTML é baixado com autenticação sem expor chave em URL.
- [x] Histórico não persiste conteúdo de fontes nem API Key.
- [x] Lint, testes e build de produção passam.
- [ ] Inspeção visual em navegador e screenshots (navegador controlável indisponível).
- [ ] Login de usuário final.

## Gate de autenticação

O backlog pede login para o site, mas não escolhe identidade própria, Google/Microsoft ou outro
provedor. Para não inferir uma política de identidade, o protótipo usa a mesma API Key da API
pública, apenas em memória. Isso é apropriado para desenvolvimento, não para usuários finais.

## Limite de upload implantado

O fluxo multipart funciona localmente. No Cloud Run, vídeos acima de 32 MiB exigem upload
direto para R2 com URL pré-assinada; esse fluxo entra na preparação de deploy e não deve ser
substituído por aumento fictício do limite HTTP.

