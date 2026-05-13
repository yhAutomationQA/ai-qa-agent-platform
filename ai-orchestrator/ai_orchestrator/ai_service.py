import structlog
from typing import Any

from ai_orchestrator.config import ai_config
from ai_orchestrator.llm.client import LLMClient
from ai_orchestrator.prompts.manager import PromptManager
from ai_orchestrator.context.builder import ContextBuilder
from ai_orchestrator.services.test_generator import TestGeneratorService
from ai_orchestrator.services.requirement_analyzer import RequirementAnalyzerService
from ai_orchestrator.core.token_tracker import TokenTracker
from ai_orchestrator.models import TestScenario, EdgeCase, NegativeScenario, RequirementSummary

logger = structlog.get_logger()


class AIService:
    def __init__(
        self,
        provider: str | None = None,
        llm_client: LLMClient | None = None,
        token_tracker: TokenTracker | None = None,
    ):
        self.token_tracker = token_tracker or TokenTracker()
        self.llm = llm_client or LLMClient(
            provider=provider,
            token_tracker=self.token_tracker,
        )
        self.prompts = PromptManager()
        self.context_builder = ContextBuilder(llm=self.llm)

        self.test_generator = TestGeneratorService(
            llm=self.llm,
            prompt_manager=self.prompts,
            context_builder=self.context_builder,
        )
        self.requirement_analyzer = RequirementAnalyzerService(
            llm=self.llm,
            prompt_manager=self.prompts,
        )

    async def generate_test_scenarios(
        self,
        requirement: str,
        context: dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> list[TestScenario]:
        return await self.test_generator.generate_test_scenarios(
            requirement=requirement,
            context=context,
            temperature=temperature,
        )

    async def generate_edge_cases(
        self,
        requirement: str,
        context: dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> list[EdgeCase]:
        return await self.test_generator.generate_edge_cases(
            requirement=requirement,
            context=context,
            temperature=temperature,
        )

    async def generate_negative_scenarios(
        self,
        requirement: str,
        context: dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> list[NegativeScenario]:
        return await self.test_generator.generate_negative_scenarios(
            requirement=requirement,
            context=context,
            temperature=temperature,
        )

    async def summarize_requirements(
        self,
        requirement: str,
        temperature: float | None = None,
    ) -> RequirementSummary:
        return await self.requirement_analyzer.summarize(
            requirement=requirement,
            temperature=temperature,
        )

    async def analyze_requirements(
        self,
        requirement: str,
    ) -> dict:
        return await self.requirement_analyzer.analyze(requirement)

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content

    def get_usage_summary(self) -> dict:
        return self.token_tracker.session_summary()

    def get_prompt_templates(self) -> list[str]:
        return self.prompts.list_templates()
