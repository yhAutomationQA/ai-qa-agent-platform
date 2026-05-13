import structlog
from typing import Any

from ai_orchestrator.exceptions import ContextBuildError
from ai_orchestrator.llm.client import LLMClient

logger = structlog.get_logger()


class ContextBuilder:
    def __init__(self, llm: LLMClient | None = None):
        self._llm = llm

    async def build(self, requirement: str, enrich: bool = True) -> dict:
        if not requirement or not requirement.strip():
            raise ContextBuildError("Requirement text is empty")

        context: dict[str, Any] = {
            "raw_requirement": requirement,
            "word_count": len(requirement.split()),
            "char_count": len(requirement),
            "has_code_blocks": "```" in requirement,
            "sentences": self._count_sentences(requirement),
        }

        if enrich and self._llm:
            try:
                domain = await self._infer_domain(requirement)
                context["domain"] = domain
            except Exception as e:
                logger.warning("domain_inference_failed", error=str(e))
                context["domain"] = "general"

        logger.debug("context_built", word_count=context["word_count"], domain=context.get("domain"))
        return context

    def build_sync(self, requirement: str) -> dict:
        return {
            "raw_requirement": requirement,
            "word_count": len(requirement.split()),
            "char_count": len(requirement),
            "has_code_blocks": "```" in requirement,
            "sentences": self._count_sentences(requirement),
            "domain": "general",
        }

    async def _infer_domain(self, text: str) -> str:
        if not self._llm:
            return "general"

        prompt = (
            f"Classify the domain of this requirement into one word "
            f"(web, mobile, api, database, security, performance, or general):\n\n{text[:1000]}"
        )
        response = await self._llm.generate(prompt, temperature=0.1, max_tokens=20)
        domain = response.content.strip().lower()
        valid = {"web", "mobile", "api", "database", "security", "performance", "general"}
        return domain if domain in valid else "general"

    def _count_sentences(self, text: str) -> int:
        import re
        return len(re.findall(r"[.!?]+", text)) or 1

    def merge(self, requirement: str, extra: dict | None = None) -> dict:
        context = self.build_sync(requirement)
        if extra:
            context.update(extra)
        return context
