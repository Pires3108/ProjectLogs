import json

VALID_ANALYSIS = {
    "objetivo": "Planejar a publicação da primeira versão.",
    "resumo": "A equipe definiu uma entrega sintética.",
    "itens": [
        {
            "titulo": "Preparar documentação",
            "descricao": "Documentar o procedimento de publicação.",
            "status": "pendente",
            "responsavel": "Equipe de documentação",
            "complexidade": "incerta",
            "evidencias": ["A documentação foi atribuída à equipe."],
            "exemplos": [],
        }
    ],
    "decisoes": ["Publicar somente após os testes."],
    "riscos": ["Prazo ainda não definido."],
    "termos_incertos": ["Data da publicação"],
    "visuais": [],
    "glossario": [],
    "linha_do_tempo": [],
    "responsabilidades": [],
}

VALID_ANALYSIS_JSON = json.dumps(VALID_ANALYSIS, ensure_ascii=False)
