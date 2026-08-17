# ADR 002 — Contrato do export Read.AI

- Status: decidido a partir de export real fornecido pelo responsável do projeto
- Contexto: Sprint 2

O backlog exige parser do export Read.AI, mas não define formato, versão, campos nem exemplos.
Criar um parser por suposição pode aceitar dados incorretamente, perder locutores ou associar
timestamps errados.

O formato observado contém título e data nas primeiras linhas, seguidos por blocos no formato
`minuto:segundo - locutor` e um ou mais parágrafos de fala. O parser preserva locutor,
timestamp inicial e texto, aceita reuniões com mais de uma hora e converte a data PT-BR quando
reconhecida.

A fixture do teste é inteiramente sintética. O arquivo real fornecido foi apenas inspecionado e
não foi copiado para o repositório.
