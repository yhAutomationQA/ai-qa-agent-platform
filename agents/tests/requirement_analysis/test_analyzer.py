import pytest
import json

from agents.src.requirement_analysis.analyzer import RequirementAnalyzer
from agents.src.requirement_analysis.models import RequirementAnalysisInput


class FakeLLMResponse:
    def __init__(self, content: str, token_count: int = 150):
        self.content = content
        self.token_usage = type("obj", (object,), {"total_tokens": token_count})()
        self.finish_reason = "stop"
        self.raw_response = None


class FakeLLMClient:
    def __init__(self, response_text: str = "", model: str = "gpt-4o"):
        self.response_text = response_text
        self.model_name = model

    async def generate(self, prompt: str, system_prompt: str | None = None, temperature: float | None = None):
        return FakeLLMResponse(content=self.response_text)


SAMPLE_GOOD_RESPONSE = json.dumps({
    "summary": {
        "overall_purpose": "Allow users to log in with email and password",
        "key_functionality": ["Email/password authentication", "Error handling for invalid credentials", "Session management"],
        "stakeholders": ["End users", "Security team"],
        "dependencies": ["User database", "Authentication service"],
        "complexity": "low",
    },
    "functional_scenarios": [
        {
            "title": "Successful login with valid credentials",
            "description": "User enters correct email and password",
            "preconditions": ["User exists", "Account is active"],
            "steps": ["Navigate to login page", "Enter valid email", "Enter valid password", "Click submit"],
            "expected_result": "User is redirected to dashboard",
            "relates_to_ac": "AC1",
            "priority": "high",
        }
    ],
    "edge_cases": [
        {
            "title": "Maximum email length",
            "description": "Email exactly at max length",
            "input_condition": "Email = 254 characters",
            "expected_behavior": "Login succeeds if valid format",
            "severity": "medium",
            "category": "boundary",
        }
    ],
    "negative_scenarios": [
        {
            "title": "SQL injection in email field",
            "description": "Attempt SQL injection via email",
            "malicious_input": "' OR '1'='1",
            "expected_failure": "Request rejected with 400",
            "attack_vector": "injection",
            "severity": "critical",
        }
    ],
    "risk_areas": [
        {
            "area": "Authentication security",
            "description": "Brute force attack on login",
            "likelihood": "medium",
            "impact": "high",
            "mitigation": "Rate limiting and account lockout",
        }
    ],
    "missing_requirements": [
        {
            "title": "Password strength indicator",
            "description": "No UI feedback for password strength during registration",
            "rationale": "Improves security UX",
            "suggested_action": "Add real-time password strength meter",
            "priority": "medium",
        }
    ],
})


class TestRequirementAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_returns_structured_output(self):
        llm = FakeLLMClient(response_text=SAMPLE_GOOD_RESPONSE)
        analyzer = RequirementAnalyzer(llm_client=llm)

        inp = RequirementAnalysisInput(
            issue_key="PROJ-123",
            summary="User login feature",
            description="As a user I want to log in",
            acceptance_criteria=["AC1: Valid credentials redirect to dashboard", "AC2: Invalid shows error"],
            comments=[],
        )

        output = await analyzer.analyze(inp)

        assert output.summary.overall_purpose == "Allow users to log in with email and password"
        assert output.summary.complexity == "low"
        assert len(output.functional_scenarios) == 1
        assert output.functional_scenarios[0].id == "FS-01"
        assert len(output.edge_cases) == 1
        assert output.edge_cases[0].id == "EC-01"
        assert len(output.negative_scenarios) == 1
        assert output.negative_scenarios[0].id == "NS-01"
        assert len(output.risk_areas) == 1
        assert len(output.missing_requirements) == 1

    @pytest.mark.asyncio
    async def test_analyze_with_minimal_input(self):
        llm = FakeLLMClient(response_text=json.dumps({
            "summary": {"overall_purpose": "Test", "key_functionality": [], "stakeholders": [], "dependencies": [], "complexity": "low"},
            "functional_scenarios": [],
            "edge_cases": [],
            "negative_scenarios": [],
            "risk_areas": [],
            "missing_requirements": [],
        }))
        analyzer = RequirementAnalyzer(llm_client=llm)

        inp = RequirementAnalysisInput(summary="Minimal")
        output = await analyzer.analyze(inp)
        assert output.summary.overall_purpose == "Test"
        assert output.metadata.source_issue_key == ""

    @pytest.mark.asyncio
    async def test_analyze_strips_code_fences(self):
        text = "```json\n" + SAMPLE_GOOD_RESPONSE + "\n```"
        llm = FakeLLMClient(response_text=text)
        analyzer = RequirementAnalyzer(llm_client=llm)

        inp = RequirementAnalysisInput(summary="Test", issue_key="X-1")
        output = await analyzer.analyze(inp)
        assert len(output.functional_scenarios) == 1

    @pytest.mark.asyncio
    async def test_analyze_metadata(self):
        llm = FakeLLMClient(response_text=SAMPLE_GOOD_RESPONSE, model="gpt-4o")
        analyzer = RequirementAnalyzer(llm_client=llm)

        inp = RequirementAnalysisInput(summary="Test", issue_key="PROJ-1")
        output = await analyzer.analyze(inp)

        assert output.metadata.source_issue_key == "PROJ-1"
        assert output.metadata.model_used == "gpt-4o"
        assert output.metadata.processing_time_ms > 0
        assert output.metadata.total_tokens > 0

    def test_build_prompt_includes_all_fields(self):
        llm = FakeLLMClient()
        analyzer = RequirementAnalyzer(llm_client=llm)

        inp = RequirementAnalysisInput(
            issue_key="K-1",
            summary="Test summary",
            description="Test desc",
            acceptance_criteria=["AC1", "AC2"],
            comments=[{"author": {"displayName": "Alice"}, "body": "Looks good"}],
            labels=["frontend"],
            priority="high",
        )

        prompt = analyzer._build_prompt(inp)
        assert "K-1" in prompt
        assert "Test summary" in prompt
        assert "Test desc" in prompt
        assert "AC1" in prompt
        assert "Alice" in prompt
        assert "high" in prompt
