import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.schemas.jira import (
    JiraAuth,
    JiraIssue,
    JiraIssueFields,
    JiraIssueType,
    JiraPriority,
    JiraStatus,
    JiraComment,
    JiraUser,
)
from agents.src.requirement_analysis.agent import RequirementAnalysisAgent
from agents.src.requirement_analysis.models import (
    RequirementAnalysisOutput,
    RequirementSummary,
    FunctionalScenario,
    EdgeCase,
    NegativeScenario,
    RiskArea,
    MissingRequirement,
    AnalysisMetadata,
)
from agents.src.base.agent import AgentResult


@pytest.fixture
def auth_headers():
    return {
        "X-Jira-Url": "https://test.atlassian.net",
        "X-Jira-Email": "test@example.com",
        "X-Jira-Token": "fake-token",
    }


@pytest.fixture
def mock_jira_issue():
    return JiraIssue(
        id="100",
        key="PROJ-123",
        fields=JiraIssueFields(
            summary="User login feature",
            description="As a user, I want to log in with my credentials",
            issuetype=JiraIssueType(name="Story"),
            priority=JiraPriority(name="High"),
            status=JiraStatus(name="In Progress", category="In Progress"),
            labels=["auth", "frontend"],
        ),
    )


@pytest.fixture
def mock_analysis_output():
    return RequirementAnalysisOutput(
        summary=RequirementSummary(
            overall_purpose="Enable user authentication",
            complexity="medium",
            key_functionality=["Login with credentials", "Session management"],
        ),
        functional_scenarios=[
            FunctionalScenario(title="Valid login with correct credentials", steps=["Enter username", "Enter password", "Click login"], expected_result="User is redirected to dashboard", priority="high"),
            FunctionalScenario(title="Logout clears session", steps=["Click logout"], expected_result="User is logged out", priority="high"),
        ],
        edge_cases=[
            EdgeCase(title="Very long password", description="Password exceeding max length", category="boundary", severity="low"),
        ],
        negative_scenarios=[
            NegativeScenario(title="SQL injection in username", description="Attempt SQL injection via username field", attack_vector="input_validation"),
        ],
        risk_areas=[
            RiskArea(area="Security", description="Brute force attacks on login", likelihood="high", impact="high", mitigation="Rate limiting + CAPTCHA"),
        ],
        missing_requirements=[
            MissingRequirement(title="Password reset flow", description="No mechanism for forgotten passwords", priority="high"),
        ],
        metadata=AnalysisMetadata(model_used="gpt-4o", total_tokens=500, processing_time_ms=150.0, source_issue_key="PROJ-123"),
    )


@pytest.mark.asyncio
async def test_analyze_requirements_full_pipeline(auth_headers, mock_jira_issue, mock_analysis_output):
    mock_comments = [
        JiraComment(id="1", body="Needs SSO support", author=JiraUser(account_id="u1", display_name="Alice")),
    ]

    with (
        patch("app.services.jira_service.JiraService.get_issue", new=AsyncMock(return_value=mock_jira_issue)),
        patch("app.services.jira_service.JiraService.get_acceptance_criteria") as mock_ac,
        patch("app.services.jira_service.JiraService.get_comments", new=AsyncMock(return_value=mock_comments)),
        patch.object(RequirementAnalysisAgent, "run", new=AsyncMock(return_value=AgentResult(status="passed", data=mock_analysis_output.model_dump()))),
    ):
        mock_ac.return_value.criteria = ["AC1: Valid login works", "AC2: Invalid shows error"]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analysis/requirements/PROJ-123",
                headers=auth_headers,
            )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["overall_purpose"] == "Enable user authentication"
    assert data["summary"]["complexity"] == "medium"
    assert len(data["functional_scenarios"]) == 2
    assert len(data["edge_cases"]) == 1
    assert len(data["negative_scenarios"]) == 1
    assert len(data["risk_areas"]) == 1
    assert len(data["missing_requirements"]) == 1
    assert data["metadata"]["source_issue_key"] == "PROJ-123"


@pytest.mark.asyncio
async def test_analyze_requirements_from_text(mock_analysis_output):
    with patch.object(RequirementAnalysisAgent, "run", new=AsyncMock(return_value=AgentResult(status="passed", data=mock_analysis_output.model_dump()))):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/analysis/requirements/from-text",
                params={
                    "summary": "User login feature",
                    "description": "As a user, I want to log in",
                    "acceptance_criteria": "Valid login works, Invalid shows error",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["overall_purpose"] == "Enable user authentication"
    assert data["summary"]["complexity"] == "medium"


@pytest.mark.asyncio
async def test_analyze_requirements_agent_error(auth_headers, mock_jira_issue):
    with (
        patch("app.services.jira_service.JiraService.get_issue", new=AsyncMock(return_value=mock_jira_issue)),
        patch("app.services.jira_service.JiraService.get_acceptance_criteria") as mock_ac,
        patch("app.services.jira_service.JiraService.get_comments", new=AsyncMock(return_value=[])),
        patch.object(RequirementAnalysisAgent, "run", new=AsyncMock(return_value=AgentResult(status="error", data={}, error="LLM processing failed"))),
    ):
        mock_ac.return_value.criteria = ["AC1"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analysis/requirements/PROJ-123",
                headers=auth_headers,
            )

    assert response.status_code == 500
    data = response.json()
    assert "LLM processing failed" in str(data)


@pytest.mark.asyncio
async def test_analyze_requirements_no_comments(auth_headers, mock_jira_issue, mock_analysis_output):
    with (
        patch("app.services.jira_service.JiraService.get_issue", new=AsyncMock(return_value=mock_jira_issue)),
        patch("app.services.jira_service.JiraService.get_acceptance_criteria") as mock_ac,
        patch.object(RequirementAnalysisAgent, "run", new=AsyncMock(return_value=AgentResult(status="passed", data=mock_analysis_output.model_dump()))),
    ):
        mock_ac.return_value.criteria = ["AC1"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analysis/requirements/PROJ-123?include_comments=false",
                headers=auth_headers,
            )

    assert response.status_code == 200
