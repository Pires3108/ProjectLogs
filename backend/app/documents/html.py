import random
import re
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from app.analysis.models import Complexity, StructuredAnalysis, VisualDefinition, VisualType
from app.documents.configuration import PROFILE_RULES, ValidatedConfiguration
from app.errors import ApiError
from app.models import DocumentProfile

SAFE_MERMAID_TEXT = re.compile(r"[^\wÀ-ÿ .,:;!?()/-]", re.UNICODE)

_COMPLEXITY_LEVELS: dict[Complexity, tuple[str, str]] = {
    Complexity.baixa: ("Simples", "simples"),
    Complexity.media: ("Intermediário", "intermediario"),
    Complexity.alta: ("Complexo", "complexo"),
    Complexity.incerta: ("A confirmar", "a-confirmar"),
}
_DEFAULT_LEVEL = _COMPLEXITY_LEVELS[Complexity.baixa]
_DECISION_LEVEL = _COMPLEXITY_LEVELS[Complexity.media]
_GENERIC_DISTRACTORS = [
    "Não foi mencionado na conversa analisada.",
    "É o oposto do que foi discutido na conversa.",
    "Não há relação direta com o restante do conteúdo.",
]
_MAX_OPTIONS = 4


class HtmlGenerator:
    def __init__(self, *, mermaid_asset_path: str) -> None:
        self.mermaid_asset_path = Path(mermaid_asset_path)
        self.environment = Environment(
            loader=PackageLoader("app.documents", "templates"),
            autoescape=select_autoescape(("html", "xml")),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(
        self,
        analysis: StructuredAnalysis,
        configuration: ValidatedConfiguration,
        *,
        visual_identity_override: str | None = None,
    ) -> str:
        visuals = self._enabled_visuals(analysis, configuration)
        mermaid_runtime = self._load_mermaid() if visuals else None
        template = self.environment.get_template(f"{configuration.perfil.value}.html")
        return template.render(
            analysis=analysis,
            configuration=configuration,
            rules=PROFILE_RULES[configuration.perfil],
            visuals=[(visual, self._to_mermaid(visual)) for visual in visuals],
            mermaid_runtime=mermaid_runtime,
            example_items=[item for item in analysis.itens if item.exemplos],
            quiz_items=self._build_quiz(analysis, configuration),
            complexity_levels=_COMPLEXITY_LEVELS,
            visual_identity_override=visual_identity_override,
        )

    def _load_mermaid(self) -> str:
        try:
            return self.mermaid_asset_path.read_text(encoding="utf-8")
        except OSError as exception:
            raise ApiError(
                status_code=500,
                code="MERMAID_ASSET_UNAVAILABLE",
                message="O recurso de diagramas não está disponível.",
            ) from exception

    @staticmethod
    def _enabled_visuals(
        analysis: StructuredAnalysis, configuration: ValidatedConfiguration
    ) -> list[VisualDefinition]:
        return [
            visual
            for visual in analysis.visuais
            if (
                (visual.tipo is VisualType.fluxograma and configuration.toggles.fluxogramas)
                or (visual.tipo is VisualType.diagrama and configuration.toggles.diagramas)
            )
            and visual.nos
            and visual.conexoes
        ]

    @staticmethod
    def _build_quiz(
        analysis: StructuredAnalysis, configuration: ValidatedConfiguration
    ) -> list[dict[str, object]]:
        is_estudo = configuration.perfil is DocumentProfile.estudo
        if not is_estudo or not configuration.toggles.exercicios:
            return []

        entries: list[tuple[str, str, tuple[str, str]]] = [
            (
                f"O que caracteriza: {item.titulo}?",
                item.descricao,
                _COMPLEXITY_LEVELS[item.complexidade],
            )
            for item in analysis.itens
        ]
        if configuration.toggles.glossario:
            entries += [
                (f'Qual é a definição de "{term.termo}"?', term.definicao, _DEFAULT_LEVEL)
                for term in analysis.glossario
            ]
        if not entries:
            entries.append(
                ("Qual é o objetivo principal desta conversa?", analysis.objetivo, _DEFAULT_LEVEL)
            )
            entries += [
                (
                    f'Por que esta decisão faz sentido: "{decision}"?',
                    analysis.objetivo,
                    _DECISION_LEVEL,
                )
                for decision in analysis.decisoes
            ]

        answers = [correct for _, correct, _ in entries]
        quiz: list[dict[str, object]] = []
        for index, (question, correct, (level, level_slug)) in enumerate(entries):
            others = [
                answer for i, answer in enumerate(answers) if i != index and answer != correct
            ]
            distractors = random.sample(others, k=min(_MAX_OPTIONS - 1, len(others)))
            if len(distractors) < min(2, _MAX_OPTIONS - 1):
                filler = [d for d in _GENERIC_DISTRACTORS if d not in distractors]
                distractors += random.sample(
                    filler, k=min(_MAX_OPTIONS - 1 - len(distractors), len(filler))
                )
            options = [{"text": correct, "correct": True}] + [
                {"text": distractor, "correct": False} for distractor in distractors
            ]
            random.shuffle(options)
            quiz.append(
                {
                    "question": question,
                    "level": level,
                    "level_slug": level_slug,
                    "options": options,
                }
            )
        return quiz

    @staticmethod
    def _to_mermaid(visual: VisualDefinition) -> str:
        direction = "TD" if visual.tipo is VisualType.fluxograma else "LR"
        id_map = {node.id: f"n{index}" for index, node in enumerate(visual.nos)}
        lines = [f"flowchart {direction}"]
        for node in visual.nos:
            label = SAFE_MERMAID_TEXT.sub("", node.rotulo)[:160]
            lines.append(f'  {id_map[node.id]}["{label}"]')
        for connection in visual.conexoes:
            if connection.origem not in id_map or connection.destino not in id_map:
                continue
            label = SAFE_MERMAID_TEXT.sub("", connection.rotulo or "")[:100]
            arrow = f" -->|{label}| " if label else " --> "
            lines.append(f"  {id_map[connection.origem]}{arrow}{id_map[connection.destino]}")
        return "\n".join(lines)
