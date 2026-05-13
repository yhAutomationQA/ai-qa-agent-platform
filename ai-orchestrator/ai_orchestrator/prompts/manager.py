from pathlib import Path
import structlog
from jinja2 import Template, TemplateError

from ai_orchestrator.exceptions import PromptTemplateError

logger = structlog.get_logger()

TEMPLATE_DIR = Path(__file__).parent / "templates"


class PromptManager:
    def __init__(self, template_dir: str | Path | None = None):
        self.template_dir = Path(template_dir) if template_dir else TEMPLATE_DIR
        if not self.template_dir.exists():
            self.template_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Template] = {}

    def render(self, template_name: str, **variables: str | dict | list) -> str:
        template = self._load(template_name)
        try:
            return template.render(**variables)
        except TemplateError as e:
            raise PromptTemplateError(f"Failed to render '{template_name}': {e}")

    def register(self, name: str, content: str) -> None:
        path = self.template_dir / f"{name}.j2"
        path.write_text(content)
        self._cache.pop(name, None)
        logger.info("template_registered", name=name)

    def get(self, name: str) -> str:
        path = self.template_dir / f"{name}.j2"
        if not path.exists():
            raise PromptTemplateError(f"Template not found: {name}")
        return path.read_text()

    def list_templates(self) -> list[str]:
        return sorted(p.stem for p in self.template_dir.glob("*.j2"))

    def _load(self, name: str) -> Template:
        if name not in self._cache:
            source = self.get(name)
            self._cache[name] = Template(source)
        return self._cache[name]
