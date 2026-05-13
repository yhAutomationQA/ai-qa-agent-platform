import pytest

from agents.src.base.agent import AgentConfig, AgentResult


def test_agent_config_defaults():
    config = AgentConfig()
    assert config.name == ""
    assert config.timeout == 300
    assert config.max_retries == 3
    assert config.headless is True


def test_agent_result_defaults():
    result = AgentResult()
    assert result.status == "pending"
    assert result.data == {}
    assert result.error is None
