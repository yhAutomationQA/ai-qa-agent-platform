import pytest
from unittest.mock import AsyncMock, patch

from ai_orchestrator.ai_service import AIService
from ai_orchestrator.config import ai_config


@pytest.fixture
def ai_service():
    return AIService(provider="openai")


class TestAIServiceInitialization:
    def test_default_provider(self):
        service = AIService()
        assert service.llm.provider.provider_name == ai_config.LLM_PROVIDER

    def test_custom_provider(self):
        service = AIService(provider="openai")
        assert service.llm.provider.provider_name == "openai"

    def test_invalid_provider(self):
        from ai_orchestrator.exceptions import ConfigurationError
        from ai_orchestrator.llm.client import LLMClient
        with pytest.raises(ConfigurationError):
            LLMClient(provider="invalid_provider")


class TestAIServicePublicAPI:
    def test_service_has_required_methods(self, ai_service: AIService):
        assert hasattr(ai_service, "generate_test_scenarios")
        assert hasattr(ai_service, "generate_edge_cases")
        assert hasattr(ai_service, "generate_negative_scenarios")
        assert hasattr(ai_service, "summarize_requirements")
        assert hasattr(ai_service, "analyze_requirements")
        assert hasattr(ai_service, "generate")
        assert hasattr(ai_service, "get_usage_summary")
        assert hasattr(ai_service, "get_prompt_templates")

    def test_usage_summary_empty(self, ai_service: AIService):
        summary = ai_service.get_usage_summary()
        assert summary["total_calls"] == 0
        assert summary["total_tokens"] == 0

    def test_prompt_templates_loaded(self, ai_service: AIService):
        templates = ai_service.get_prompt_templates()
        assert "test_scenarios" in templates
        assert "summarize_requirements" in templates
        assert "edge_cases" in templates
        assert "negative_scenarios" in templates
