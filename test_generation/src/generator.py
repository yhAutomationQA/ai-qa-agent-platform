from __future__ import annotations

import json
import structlog
from typing import Any

from .models import (
    TestGenerationInput,
    TestGenerationOutput,
    GeneratedTestFile,
    TestDataSuggestion,
    TestType,
)
from .config import config
from .utils import build_context_block, clean_code_block
from .prompts import (
    PLAYWRIGHT_UI_SYSTEM_PROMPT,
    PLAYWRIGHT_UI_PROMPT_TEMPLATE,
    API_TEST_SYSTEM_PROMPT,
    API_TEST_PROMPT_TEMPLATE,
    TEST_DATA_SYSTEM_PROMPT,
    TEST_DATA_PROMPT_TEMPLATE,
)
from .playwright_codegen import PlaywrightCodeGenerator
from .api_codegen import ApiCodeGenerator
from .data_suggestions import DataSuggestionEngine

logger = structlog.get_logger()


class TestGenerator:
    def __init__(
        self,
        llm_client: Any | None = None,
        pw_codegen: PlaywrightCodeGenerator | None = None,
        api_codegen: ApiCodeGenerator | None = None,
        data_engine: DataSuggestionEngine | None = None,
    ):
        self._llm = llm_client
        self.pw_codegen = pw_codegen or PlaywrightCodeGenerator()
        self.api_codegen = api_codegen or ApiCodeGenerator()
        self.data_engine = data_engine or DataSuggestionEngine()

    @property
    def llm(self) -> Any:
        if self._llm is None:
            from ai_orchestrator.llm.client import LLMClient
            self._llm = LLMClient()
        return self._llm

    async def generate(
        self,
        input_data: TestGenerationInput,
    ) -> TestGenerationOutput:
        logger.info(
            "generating_tests",
            summary=input_data.requirement_summary[:60],
            test_types=[t.value for t in input_data.test_types],
        )

        context = build_context_block(input_data)
        ui_tests: list[GeneratedTestFile] = []
        api_tests: list[GeneratedTestFile] = []
        data_suggestions: list[TestDataSuggestion] = []
        total_prompt = 0
        total_completion = 0

        if TestType.UI in input_data.test_types or TestType.BOTH in input_data.test_types:
            ui_result = await self._generate_ui_tests(input_data, context)
            ui_tests.extend(ui_result.get("files", []))
            total_prompt += ui_result.get("prompt_tokens", 0)
            total_completion += ui_result.get("completion_tokens", 0)

        if TestType.API in input_data.test_types or TestType.BOTH in input_data.test_types:
            api_result = await self._generate_api_tests(input_data, context)
            api_tests.extend(api_result.get("files", []))
            total_prompt += api_result.get("prompt_tokens", 0)
            total_completion += api_result.get("completion_tokens", 0)

        data_result = await self._generate_test_data(input_data, context)
        data_suggestions.extend(data_result.get("suggestions", []))
        total_prompt += data_result.get("prompt_tokens", 0)
        total_completion += data_result.get("completion_tokens", 0)

        summary_parts = []
        if ui_tests:
            summary_parts.append(f"{len(ui_tests)} UI test files")
        if api_tests:
            summary_parts.append(f"{len(api_tests)} API test files")
        if data_suggestions:
            summary_parts.append(f"{len(data_suggestions)} data suggestions")

        summary = (
            f"Generated {', '.join(summary_parts)} for: {input_data.requirement_summary[:80]}"
        )

        return TestGenerationOutput(
            ui_tests=ui_tests,
            api_tests=api_tests,
            test_data_suggestions=data_suggestions,
            summary=summary,
            prompt_tokens=total_prompt,
            completion_tokens=total_completion,
            model_used=config.LLM_MODEL,
        )

    async def _generate_ui_tests(
        self,
        input_data: TestGenerationInput,
        context: str,
    ) -> dict[str, Any]:
        try:
            prompt = PLAYWRIGHT_UI_PROMPT_TEMPLATE.format(
                context=context,
                tech=input_data.technology_stack.value,
                viewport_width=config.DEFAULT_VIEWPORT_WIDTH,
                viewport_height=config.DEFAULT_VIEWPORT_HEIGHT,
                timeout=config.DEFAULT_TIMEOUT,
            )

            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=PLAYWRIGHT_UI_SYSTEM_PROMPT,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
            )

            llm_data: dict[str, Any] = {}
            try:
                parsed = json.loads(clean_code_block(response.content))
                if isinstance(parsed, dict):
                    llm_data = parsed
                else:
                    llm_data = {"code": response.content}
            except json.JSONDecodeError:
                llm_data = {"code": response.content}

            files = self.pw_codegen.generate_from_llm_output(input_data, llm_data)

            return {
                "files": files,
                "prompt_tokens": response.token_usage.prompt_tokens if response.token_usage else 0,
                "completion_tokens": response.token_usage.completion_tokens if response.token_usage else 0,
            }
        except Exception as e:
            logger.error("ui_test_generation_failed", error=str(e))
            return {"files": [], "prompt_tokens": 0, "completion_tokens": 0}

    async def _generate_api_tests(
        self,
        input_data: TestGenerationInput,
        context: str,
    ) -> dict[str, Any]:
        try:
            prompt = API_TEST_PROMPT_TEMPLATE.format(context=context)

            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=API_TEST_SYSTEM_PROMPT,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
            )

            llm_data: dict[str, Any] = {}
            try:
                parsed = json.loads(clean_code_block(response.content))
                if isinstance(parsed, list):
                    llm_data = {"scenarios": parsed}
                elif isinstance(parsed, dict):
                    llm_data = parsed
                else:
                    llm_data = {"scenarios": []}
            except json.JSONDecodeError:
                llm_data = {"scenarios": []}

            files = self.api_codegen.generate_from_llm_output(input_data, llm_data)

            return {
                "files": files,
                "prompt_tokens": response.token_usage.prompt_tokens if response.token_usage else 0,
                "completion_tokens": response.token_usage.completion_tokens if response.token_usage else 0,
            }
        except Exception as e:
            logger.error("api_test_generation_failed", error=str(e))
            return {"files": [], "prompt_tokens": 0, "completion_tokens": 0}

    async def _generate_test_data(
        self,
        input_data: TestGenerationInput,
        context: str,
    ) -> dict[str, Any]:
        try:
            prompt = TEST_DATA_PROMPT_TEMPLATE.format(context=context)

            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=TEST_DATA_SYSTEM_PROMPT,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
            )

            llm_data: dict[str, Any] = {}
            try:
                parsed = json.loads(clean_code_block(response.content))
                if isinstance(parsed, list):
                    llm_data = {"suggestions": parsed}
                elif isinstance(parsed, dict):
                    llm_data = parsed
            except json.JSONDecodeError:
                pass

            suggestions = self.data_engine.parse_llm_suggestions(input_data, llm_data)

            return {
                "suggestions": suggestions,
                "prompt_tokens": response.token_usage.prompt_tokens if response.token_usage else 0,
                "completion_tokens": response.token_usage.completion_tokens if response.token_usage else 0,
            }
        except Exception as e:
            logger.error("test_data_generation_failed", error=str(e))
            suggestions = self.data_engine.suggest_for_input(input_data)
            return {"suggestions": suggestions, "prompt_tokens": 0, "completion_tokens": 0}

    async def generate_playwright_suite(
        self,
        feature_name: str,
        page_objects: list[dict[str, Any]],
        test_cases: list[dict[str, Any]],
    ) -> list[GeneratedTestFile]:
        """Generate Playwright suite from structured data without LLM."""
        return self.pw_codegen.generate_all(feature_name, page_objects, test_cases)

    async def generate_api_suite(
        self,
        scenarios: list[dict[str, Any]],
    ) -> list[GeneratedTestFile]:
        """Generate API test suite from structured scenarios without LLM."""
        return self.api_codegen.generate_all(scenarios)


