import pytest
import json

from agents.src.requirement_analysis.agent import RequirementAnalysisAgent
from agents.src.base.agent import AgentConfig


class FakeLLMResponse:
    def __init__(self, content: str = "{}", token_count: int = 50):
        self.content = content
        self.token_usage = type("obj", (object,), {"total_tokens": token_count})()
        self.finish_reason = "stop"
        self.raw_response = None


class FakeLLMClient:
    def __init__(self):
        self.model_name = "test-model"

    async def generate(self, prompt: str, system_prompt: str | None = None, temperature: float | None = None):
        return FakeLLMResponse(content=json.dumps({
            "summary": {"overall_purpose": "Test purpose", "key_functionality": ["func1"], "stakeholders": [], "dependencies": [], "complexity": "low"},
            "functional_scenarios": [{"title": "Scenario 1", "description": "desc", "preconditions": [], "steps": [], "expected_result": "ok", "relates_to_ac": "", "priority": "high"}],
            "edge_cases": [],
            "negative_scenarios": [],
            "risk_areas": [],
            "missing_requirements": [],
        }))


class TestRequirementAnalysisAgent:
    @pytest.mark.asyncio
    async def test_validate_valid_input(self):
        agent = RequirementAnalysisAgent(llm_client=FakeLLMClient())
        assert await agent.validate({"summary": "Test story"}) is True
        assert await agent.validate({"description": "Test desc"}) is True
        assert await agent.validate({"issue_key": "PROJ-1"}) is True

    @pytest.mark.asyncio
    async def test_validate_invalid_input(self):
        agent = RequirementAnalysisAgent(llm_client=FakeLLMClient())
        assert await agent.validate({}) is False
        assert await agent.validate({"irrelevant": "data"}) is False

    @pytest.mark.asyncio
    async def test_execute_returns_agent_result(self):
        agent = RequirementAnalysisAgent(llm_client=FakeLLMClient())
        result = await agent.execute({
            "issue_key": "PROJ-1",
            "summary": "Login feature",
            "description": "User login",
            "acceptance_criteria": ["AC1"],
        })
        assert result.status == "passed"
        assert "summary" in result.data
        assert "functional_scenarios" in result.data

    @pytest.mark.asyncio
    async def test_run_lifecycle(self):
        agent = RequirementAnalysisAgent(llm_client=FakeLLMClient())
        result = await agent.run({
            "summary": "Password reset",
            "description": "User can reset password via email",
        })
        assert result.status == "passed"
        assert result.duration_ms > 0
        assert result.started_at is not None
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_run_with_invalid_input(self):
        agent = RequirementAnalysisAgent(llm_client=FakeLLMClient())
        result = await agent.run({})
        assert result.status == "invalid"
        assert "validation" in result.error.lower()

    @pytest.mark.asyncio
    async def test_cleanup_does_not_raise(self):
        agent = RequirementAnalysisAgent(llm_client=FakeLLMClient())
        await agent.cleanup()
