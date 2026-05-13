import structlog
from typing import Any

from ai_orchestrator.llm.client import LLMClient
from ai_orchestrator.prompts.manager import PromptManager
from ai_orchestrator.context.builder import ContextBuilder
from ai_orchestrator.parsing.parser import ResponseParser
from ai_orchestrator.models import TestScenario, EdgeCase, NegativeScenario

logger = structlog.get_logger()


class TestGeneratorService:
    def __init__(
        self,
        llm: LLMClient,
        prompt_manager: PromptManager | None = None,
        context_builder: ContextBuilder | None = None,
    ):
        self.llm = llm
        self.prompts = prompt_manager or PromptManager()
        self.context_builder = context_builder or ContextBuilder(llm=llm)

    async def generate_test_scenarios(
        self,
        requirement: str,
        context: dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> list[TestScenario]:
        logger.info("generating_test_scenarios")

        ctx = await self.context_builder.build(requirement)
        if context:
            ctx.update(context)

        prompt = self.prompts.render(
            "test_scenarios",
            requirement=requirement,
            context=str(ctx),
        )

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt="You are a senior QA engineer. Always return valid JSON.",
            temperature=temperature,
        )

        scenarios = ResponseParser.parse_test_scenarios(response.content)

        for s in scenarios:
            s.generated_from = "requirement"

        logger.info("test_scenarios_generated", count=len(scenarios))
        return scenarios

    async def generate_edge_cases(
        self,
        requirement: str,
        context: dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> list[EdgeCase]:
        logger.info("generating_edge_cases")

        ctx = await self.context_builder.build(requirement)
        if context:
            ctx.update(context)

        prompt = self.prompts.render(
            "edge_cases",
            requirement=requirement,
            context=str(ctx),
        )

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt="You are a QA engineer specializing in boundary analysis. Always return valid JSON.",
            temperature=temperature,
        )

        cases = ResponseParser.parse_edge_cases(response.content)
        logger.info("edge_cases_generated", count=len(cases))
        return cases

    async def generate_negative_scenarios(
        self,
        requirement: str,
        context: dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> list[NegativeScenario]:
        logger.info("generating_negative_scenarios")

        ctx = await self.context_builder.build(requirement)
        if context:
            ctx.update(context)

        prompt = self.prompts.render(
            "negative_scenarios",
            requirement=requirement,
            context=str(ctx),
        )

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt="You are a security-focused QA engineer. Always return valid JSON.",
            temperature=temperature,
        )

        scenarios = ResponseParser.parse_negative_scenarios(response.content)
        logger.info("negative_scenarios_generated", count=len(scenarios))
        return scenarios
