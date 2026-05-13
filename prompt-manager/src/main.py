from pathlib import Path
import structlog
from jinja2 import Template

logger = structlog.get_logger()


class PromptManager:
    def __init__(self, templates_dir: str | Path = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, str] = {}

    def register(self, name: str, template_text: str) -> None:
        path = self.templates_dir / f"{name}.j2"
        path.write_text(template_text)
        self._cache.pop(name, None)
        logger.info("prompt_registered", name=name)

    def render(self, name: str, **variables: str) -> str:
        source = self._load(name)
        template = Template(source)
        return template.render(**variables)

    def get(self, name: str) -> str:
        return self._load(name)

    def list(self) -> list[str]:
        return [p.stem for p in self.templates_dir.glob("*.j2")]

    def delete(self, name: str) -> None:
        path = self.templates_dir / f"{name}.j2"
        if path.exists():
            path.unlink()
            self._cache.pop(name, None)
            logger.info("prompt_deleted", name=name)

    def _load(self, name: str) -> str:
        if name not in self._cache:
            path = self.templates_dir / f"{name}.j2"
            if not path.exists():
                raise FileNotFoundError(f"Prompt template not found: {name}")
            self._cache[name] = path.read_text()
        return self._cache[name]
