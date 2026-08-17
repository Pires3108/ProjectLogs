# Sprint 4 — Perfis e toggles

## Escopo entregue

- Modelos para Estudo, Organização e Backlog do projeto.
- Fonte única de regras com foco, tom, seções obrigatórias e toggles permitidos.
- Sete toggles booleanos com valores padrão desativados.
- Desativação automática de toggles fora de contexto.
- Aviso `TOGGLE_IGNORED_FOR_PROFILE` sem transformar a combinação em erro fatal.
- Endpoint de validação reutilizável pelo frontend antes de criar um job.
- Catálogo de capacidades derivado das mesmas regras usadas pelo backend.

## Regras

- Todos: fluxogramas, diagramas e exemplos.
- Estudo: exercícios e glossário.
- Organização: linha do tempo e matriz de responsabilidade.
- Backlog: matriz de responsabilidade.

## Critérios de aceite

- [x] Os três perfis possuem estrutura e tom próprios.
- [x] Combinações válidas permanecem inalteradas.
- [x] Toggles inválidos são desativados com aviso.
- [x] Campos desconhecidos e perfis inexistentes produzem validação `422` padronizada.
- [x] API e catálogo usam a mesma fonte de regras.
- [x] Contrato OpenAPI está atualizado.
- [x] Testes cobrem todos os perfis e regras específicas.
