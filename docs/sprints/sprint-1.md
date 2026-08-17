# Sprint 1 — Ingestão multi-fonte

## Escopo entregue

- Endpoint multipart para uma ou mais fontes em uma mesma ingestão.
- Registro extensível de tipos de fonte e indicação de necessidade de transcrição.
- Normalização de Markdown, DOCX, TXT, VTT e SRT.
- Extração de parágrafos e tabelas em DOCX.
- Remoção de índices, timestamps, metadados e tags de legendas.
- Limites configuráveis por categoria com leitura incremental.
- Armazenamento local persistente atrás de uma fronteira substituível.
- Identificadores opacos; nomes enviados não determinam caminhos no servidor.
- Erros padronizados para formato, corrupção, tamanho e conteúdo insuficiente.

## Critérios de aceite

- [x] Uma requisição aceita múltiplas fontes.
- [x] `.md`, `.docx`, `.txt`, `.vtt` e `.srt` produzem texto normalizado.
- [x] `.mp3`, `.wav`, `.mp4` e `.mov` são aceitos e marcados para transcrição.
- [x] Arquivos vazios, corrompidos, grandes ou não suportados são rejeitados.
- [x] Arquivos são preservados para etapas posteriores do pipeline.
- [x] Contrato OpenAPI documenta a ingestão e os erros.
- [x] Testes unitários e de API cobrem caminhos principais e regressões.

## Limite desta sprint

O storage local é a implementação de desenvolvimento. A configuração S3 compatível já está
presente na infraestrutura, mas a troca do adaptador depende da persistência de jobs e será
integrada com o pipeline assíncrono. Áudio e vídeo ainda não são decodificados; ficam
armazenados e sinalizados para a Sprint 2.
