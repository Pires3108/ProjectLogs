import re
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from app.analysis.models import StructuredAnalysis, VisualDefinition, VisualType
from app.documents.configuration import PROFILE_RULES, ValidatedConfiguration
from app.errors import ApiError

SAFE_MERMAID_TEXT = re.compile(r"[^\wÀ-ÿ .,:;!?()/-]", re.UNICODE)


class HtmlGenerator:
    def __init__(self, *, mermaid_asset_path: str) -> None:
        self.mermaid_asset_path = Path(mermaid_asset_path)
        self.environment = Environment(
            loader=PackageLoader("app.documents", "templates"),
            autoescape=select_autoescape(("html", "xml")),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, analysis: StructuredAnalysis, configuration: ValidatedConfiguration) -> str:
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
