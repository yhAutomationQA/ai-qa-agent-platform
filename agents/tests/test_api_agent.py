import pytest

from agents.src.api.agent import APIAgent
from agents.src.base.agent import AgentConfig


@pytest.mark.asyncio
async def test_api_agent_validation():
    agent = APIAgent()
    assert await agent.validate({"method": "GET", "url": "http://test.com"}) is True
    assert await agent.validate({"method": "GET"}) is False
    assert await agent.validate({"url": "http://test.com"}) is False
