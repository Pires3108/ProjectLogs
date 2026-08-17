# Sprint 2 — Transcrição e Read.AI

## Escopo entregue

- Contrato de transcrição independente de fornecedor.
- Adaptador Groq para `whisper-large-v3-turbo`.
- Extração de áudio com FFmpeg em mono, 16 kHz e 32 kbps.
- Divisão em blocos de 20 minutos para respeitar o limite gratuito de upload.
- Recomposição dos timestamps dos blocos no resultado final.
- Resultado estruturado com texto, segmentos, duração, idioma, modelo e provedor.
- Parser do export TXT de transcrição do Read.AI.
- Detecção automática do export Read.AI durante a ingestão.
- Tratamento padronizado de ausência de configuração e indisponibilidade do provedor.

## Evidência com os arquivos fornecidos

O arquivo real foi lido fora do repositório e reconhecido com 85 blocos de fala, data válida e
último timestamp em 2.275 segundos. O vídeo associado possui aproximadamente 206 MB, por isso
não cabe no limite de 25 MB por upload do free tier e justifica o pré-processamento em blocos.
Nenhum nome, fala, token ou conteúdo real foi copiado para fixtures, documentação ou logs.

## Critérios de aceite

- [x] Áudio e vídeo armazenados podem ser resolvidos para transcrição por ID opaco.
- [x] O provedor é substituível sem alterar o serviço de domínio.
- [x] Arquivos grandes são convertidos e divididos antes do envio.
- [x] Falhas externas viram erros padronizados sem expor a reunião.
- [x] Export Read.AI preserva locutor, timestamp e texto.
- [x] Fixtures são sintéticas e testes não dependem de credenciais externas.
- [ ] Chamada real ao Groq em staging (depende de `GROQ_API_KEY` e ambiente implantado).

## Próxima integração

A execução será conectada a jobs Celery quando a persistência e a fila forem implementadas. Até
lá, a integração é exercitada por testes de contrato HTTP com transporte simulado.
