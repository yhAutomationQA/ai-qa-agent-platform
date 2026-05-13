import structlog
from typing import Any

from ai_orchestrator.llm.client import LLMClient
from ai_orchestrator.prompts.manager import PromptManager
from ai_orchestrator.parsing.parser import ResponseParser
from ai_orchestrator.models import RequirementSummary

logger = structlog.get_logger()


class RequirementAnalyzerService:
    def __init__(
        self,
        llm: LLMClient,
        prompt_manager: PromptManager | None = None,
    ):
        self.llm = llm
        self.prompts = prompt_manager or PromptManager()

    async def summarize(
        self,
        requirement: str,
        temperature: float | None = None,
    ) -> RequirementSummary:
        logger.info("summarizing_requirements")

        prompt = self.prompts.render(
            "summarize_requirements",
            requirement=requirement,
        )

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt="You are a business analyst. Always return valid JSON.",
            temperature=temperature,
        )

        data = ResponseParser.parse_requirement_summary(response.content)

        summary = RequirementSummary(
            original_length=len(requirement),
            summary=data.get("summary", ""),
            key_points=data.get("key_points", []),
            stakeholders=data.get("stakeholders", []),
            dependencies=data.get("dependencies", []),
            risk_areas=data.get("risk_areas", []),
            estimated_effort=data.get("estimated_effort", "medium"),
        )

        logger.info(
            "requirements_summarized",
            key_points=len(summary.key_points),
            risk_areas=len(summary.risk_areas),
        )

        return summary

    async def analyze(self, requirement: str) -> dict:
        summary = await self.summarize(requirement)
        token_count = self.llm.count_tokens(requirement)

        return {
            "summary": summary.summary,
            "key_points": summary.key_points,
            "stakeholders": summary.stakeholders,
            "dependencies": summary.dependencies,
            "risk_areas": summary.risk_areas,
            "estimated_effort": summary.estimated_effort,
            "metrics": {
                "original_length": summary.original_length,
                "word_count": len(requirement.split()),
                "token_count": token_count,
            },
        }
