import pytest

from ai_orchestrator.src.config import OrchestratorConfig


@pytest.fixture
def config():
    return OrchestratorConfig()


@pytest.mark.asyncio
async def test_config_defaults(config: OrchestratorConfig):
    assert config.LLM_PROVIDER == "openai"
    assert config.OPENAI_MODEL == "gpt-4o"
    assert config.LLM_RETRY_MAX_ATTEMPTS == 3
