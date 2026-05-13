import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from test_generation.src.generator import TestGenerator
from test_generation.src.models import TestGenerationInput, TestType


class TestTestGenerator:
    @pytest.mark.asyncio
    async def test_generate_returns_expected_structure(self):
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(
            return_value=MagicMock(
                content='{"code": "test content"}',
                token_usage=MagicMock(prompt_tokens=50, completion_tokens=100),
            )
        )
        gen = TestGenerator(llm_client=mock_llm)
        inp = TestGenerationInput(
            requirement_summary="Login feature",
            test_types=[TestType.UI],
        )
        result = await gen.generate(inp)
        assert result.summary.startswith("Generated")
        assert isinstance(result.ui_tests, list)
        assert isinstance(result.api_tests, list)
        assert isinstance(result.test_data_suggestions, list)

    @pytest.mark.asyncio
    async def test_generate_all_test_types(self):
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(
            return_value=MagicMock(
                content="test output",
                token_usage=MagicMock(prompt_tokens=30, completion_tokens=60),
            )
        )
        gen = TestGenerator(llm_client=mock_llm)
        inp = TestGenerationInput(
            requirement_summary="Full feature",
            test_types=[TestType.UI, TestType.API],
        )
        result = await gen.generate(inp)
        assert result.prompt_tokens > 0
        assert result.completion_tokens > 0

    @pytest.mark.asyncio
    async def test_generate_playwright_suite(self):
        gen = TestGenerator(llm_client=MagicMock())
        files = await gen.generate_playwright_suite(
            feature_name="Login",
            page_objects=[
                {
                    "name": "Login",
                    "elements": [{"name": "emailInput", "selector": "#email"}],
                    "actions": [{"name": "login", "steps": ['fillField("#email", "x")']}],
                }
            ],
            test_cases=[
                {
                    "name": "should login",
                    "steps": ['loginPage.login("x", "y")'],
                }
            ],
        )
        assert len(files) >= 2
        assert any(".page.ts" in f.filename for f in files)
        assert any(".spec.ts" in f.filename for f in files)

    @pytest.mark.asyncio
    async def test_generate_api_suite(self):
        gen = TestGenerator(llm_client=MagicMock())
        files = await gen.generate_api_suite(
            scenarios=[
                {
                    "endpoint": "GET /api/health",
                    "method": "GET",
                    "path": "/api/health",
                    "tests": [{"name": "health check", "type": "positive", "expected_status": 200}],
                }
            ]
        )
        assert len(files) == 1
        assert "api-tests.spec.ts" in files[0].filename

    @pytest.mark.asyncio
    async def test_llm_failure_falls_back_gracefully(self):
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=Exception("API down"))
        gen = TestGenerator(llm_client=mock_llm)
        inp = TestGenerationInput(
            requirement_summary="Test feature",
            test_types=[TestType.UI],
        )
        result = await gen.generate(inp)
        assert len(result.ui_tests) == 0
        assert result.summary is not None
