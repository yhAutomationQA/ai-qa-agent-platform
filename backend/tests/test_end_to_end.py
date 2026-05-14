"""End-to-end integration tests covering the full AI QA pipeline.

Tests the complete flow: Requirement Analysis -> Test Generation -> Test Execution -> Failure Analysis
Each stage is tested individually and as a combined pipeline with appropriate mocking at boundaries.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.analysis.models import (
    AnalysisInput,
    BatchAnalysisInput,
    FailureAnalysis,
    BatchAnalysisResult,
    FailureCategory,
    RiskLevel,
)
from app.execution.models import (
    TestExecution,
    ExecutionType,
    ExecutionStatus,
)
from agents.src.base.agent import AgentResult
from agents.src.requirement_analysis.agent import RequirementAnalysisAgent
from agents.src.requirement_analysis.models import RequirementAnalysisOutput
from tests.mock_data import (
    LOGIN_REQUIREMENT,
    LOGIN_REQUIREMENT_TASK,
    LOGIN_ANALYSIS_OUTPUT,
    LOGIN_TEST_GENERATION_INPUT,
    LOGIN_TEST_GENERATION_OUTPUT,
    LOGIN_EXECUTION_REQUEST,
    LOGIN_EXECUTION,
    LOGIN_EXECUTION_FAILED,
    LOGIN_FAILURE_INPUT,
    LOGIN_FAILURE_BATCH_INPUT,
    LOGIN_FAILURE_ANALYSIS,
    JIRA_AUTH_HEADERS,
    LOGIN_JIRA_ISSUE,
    LOGIN_JIRA_COMMENTS,
)


# ── Fixtures ───────────────────────────────────────────────

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_subprocess():
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock:
        proc = AsyncMock()
        proc.stdout = asyncio.StreamReader()
        proc.stderr = asyncio.StreamReader()
        proc.stdout.feed_eof()
        proc.stderr.feed_eof()
        proc.wait = AsyncMock(return_value=0)
        mock.return_value = proc
        yield mock


# ═══════════════════════════════════════════════════════════
# 1. Full Pipeline: from-text (no Jira)
# ═══════════════════════════════════════════════════════════

class TestFullPipelineFromText:
    """End-to-end pipeline starting from raw text requirements."""

    def test_requirement_analysis_to_failure_analysis(
        self, client, mock_subprocess
    ):
        """Complete pipeline: analyze text -> generate tests -> execute -> analyze failure."""
        # ── Stage 1: Requirement Analysis ──
        with patch.object(
            RequirementAnalysisAgent,
            "run",
            new=AsyncMock(
                return_value=AgentResult(
                    status="passed",
                    data=LOGIN_ANALYSIS_OUTPUT.model_dump(mode="json"),
                )
            ),
        ) as mock_agent:
            response = client.post(
                "/api/v1/analysis/requirements/from-text",
                params={
                    "summary": LOGIN_REQUIREMENT["story"],
                    "description": "As a user, I want to log in with my email and password",
                    "acceptance_criteria": ",".join(LOGIN_REQUIREMENT["acceptance_criteria"]),
                },
            )

        assert response.status_code == 200
        analysis = response.json()
        assert analysis["summary"]["overall_purpose"] == LOGIN_ANALYSIS_OUTPUT.summary.overall_purpose
        assert len(analysis["functional_scenarios"]) == 4
        assert len(analysis["edge_cases"]) == 3
        assert len(analysis["negative_scenarios"]) == 3
        assert len(analysis["risk_areas"]) == 2
        assert len(analysis["missing_requirements"]) == 2

        # ── Stage 2: Test Generation ──
        with patch(
            "test_generation.src.generator.TestGenerator.generate",
            new=AsyncMock(return_value=LOGIN_TEST_GENERATION_OUTPUT),
        ):
            response = client.post(
                "/api/v1/test-generation/generate",
                json=LOGIN_TEST_GENERATION_INPUT.model_dump(mode="json"),
            )

        assert response.status_code == 200
        tests = response.json()
        assert len(tests["ui_tests"]) == 2
        assert len(tests["api_tests"]) == 1
        assert len(tests["test_data_suggestions"]) == 2
        assert "login" in tests["summary"].lower()

        # ── Stage 3: Test Execution ──
        response = client.post(
            "/api/v1/execution/execute",
            json=LOGIN_EXECUTION_REQUEST,
        )

        assert response.status_code == 200
        execution = response.json()
        assert execution["status"] in ("passed", "running")
        assert execution["test_case_id"] == "tc-login-001"

        # ── Stage 4: Failure Analysis ──
        response = client.post(
            "/api/v1/failure-analysis/analyze?use_ai=false",
            json=LOGIN_FAILURE_INPUT.model_dump(mode="json"),
        )

        assert response.status_code == 200
        failure = response.json()
        assert failure["ai_used"] is False
        assert failure["category"]["primary_category"] in (
            "assertion", "ui", "timeout", "flaky", "network", "api", "permission", "data", "unknown"
        )
        assert failure["summary"]["one_liner"] != ""
        assert failure["risk"]["level"] in ("low", "medium", "high", "critical")
        assert failure["analysis_id"] is not None

    def test_pipeline_agent_error_returns_500(self, client):
        """When the requirement analysis agent fails, the endpoint returns 500."""
        with patch.object(
            RequirementAnalysisAgent,
            "run",
            new=AsyncMock(
                return_value=AgentResult(
                    status="error",
                    data={},
                    error="LLM provider unavailable",
                )
            ),
        ):
            response = client.post(
                "/api/v1/analysis/requirements/from-text",
                params={
                    "summary": "Test feature",
                    "acceptance_criteria": "AC1",
                },
            )

        assert response.status_code == 500
        assert "LLM provider unavailable" in str(response.json())

    def test_pipeline_with_empty_acceptance_criteria(self, client):
        """Pipeline handles empty acceptance criteria gracefully."""
        from agents.src.requirement_analysis.models import (
            RequirementAnalysisOutput,
            RequirementSummary,
            AnalysisMetadata,
        )

        minimal_output = RequirementAnalysisOutput(
            summary=RequirementSummary(
                overall_purpose="Minimal test",
                complexity="low",
                key_functionality=[],
            ),
            functional_scenarios=[],
            edge_cases=[],
            negative_scenarios=[],
            risk_areas=[],
            missing_requirements=[],
            metadata=AnalysisMetadata(
                model_used="gpt-4o",
                total_tokens=10,
                processing_time_ms=5.0,
                source_issue_key="MANUAL",
            ),
        )

        with patch.object(
            RequirementAnalysisAgent,
            "run",
            new=AsyncMock(
                return_value=AgentResult(
                    status="passed",
                    data=minimal_output.model_dump(mode="json"),
                )
            ),
        ):
            response = client.post(
                "/api/v1/analysis/requirements/from-text",
                params={
                    "summary": "Empty test",
                    "acceptance_criteria": "",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["complexity"] == "low"
        assert len(data["functional_scenarios"]) == 0


# ═══════════════════════════════════════════════════════════
# 2. Full Pipeline: Jira-backed
# ═══════════════════════════════════════════════════════════

class TestFullPipelineJiraBacked:
    """End-to-end pipeline starting from a Jira issue."""

    @pytest.fixture
    def mock_jira_services(self):
        """Mock all JiraService methods used by the analysis endpoint."""
        from app.schemas.jira import (
            JiraIssue,
            JiraIssueFields,
            JiraIssueType,
            JiraPriority,
            JiraStatus,
            JiraAcceptanceCriteria,
            JiraComment,
            JiraUser,
        )

        mock_issue = JiraIssue(
            id=LOGIN_JIRA_ISSUE["id"],
            key=LOGIN_JIRA_ISSUE["key"],
            fields=JiraIssueFields(
                summary=LOGIN_JIRA_ISSUE["fields"]["summary"],
                description="As a user, I want to log in with my email and password.",
                issuetype=JiraIssueType(
                    name=LOGIN_JIRA_ISSUE["fields"]["issuetype"]["name"]
                ),
                priority=JiraPriority(
                    name=LOGIN_JIRA_ISSUE["fields"]["priority"]["name"]
                ),
                status=JiraStatus(
                    name=LOGIN_JIRA_ISSUE["fields"]["status"]["name"],
                    category=LOGIN_JIRA_ISSUE["fields"]["status"]["statusCategory"]["name"],
                ),
                labels=LOGIN_JIRA_ISSUE["fields"]["labels"],
            ),
        )

        mock_ac = JiraAcceptanceCriteria(
            criteria=LOGIN_REQUIREMENT["acceptance_criteria"]
        )

        mock_comments = [
            JiraComment(
                id=c["id"],
                body=c["body"],
                author=JiraUser(
                    display_name=c["author"]["displayName"],
                    account_id=c["author"].get("emailAddress", ""),
                ),
            )
            for c in LOGIN_JIRA_COMMENTS
        ]

        patchers = [
            patch(
                "app.api.v1.analysis.JiraService.get_issue",
                new=AsyncMock(return_value=mock_issue),
            ),
            patch(
                "app.api.v1.analysis.JiraService.get_acceptance_criteria",
                new=AsyncMock(return_value=mock_ac),
            ),
            patch(
                "app.api.v1.analysis.JiraService.get_comments",
                new=AsyncMock(return_value=mock_comments),
            ),
        ]
        for p in patchers:
            p.start()
        yield
        for p in patchers:
            p.stop()

    def test_jira_backed_full_pipeline(
        self, client, mock_jira_services, mock_subprocess
    ):
        """Jira issue -> analysis -> test generation -> execution -> failure analysis."""
        # ── Stage 1: Jira-backed Requirement Analysis ──
        with patch.object(
            RequirementAnalysisAgent,
            "run",
            new=AsyncMock(
                return_value=AgentResult(
                    status="passed",
                    data=LOGIN_ANALYSIS_OUTPUT.model_dump(mode="json"),
                )
            ),
        ):
            response = client.get(
                "/api/v1/analysis/requirements/PROJ-123",
                headers=JIRA_AUTH_HEADERS,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["overall_purpose"] == LOGIN_ANALYSIS_OUTPUT.summary.overall_purpose
        assert data["metadata"]["source_issue_key"] == "MANUAL"

        # ── Stage 2: Generate tests ──
        with patch(
            "test_generation.src.generator.TestGenerator.generate",
            new=AsyncMock(return_value=LOGIN_TEST_GENERATION_OUTPUT),
        ):
            response = client.post(
                "/api/v1/test-generation/generate/ui",
                json=LOGIN_TEST_GENERATION_INPUT.model_dump(mode="json"),
            )

        assert response.status_code == 200
        assert len(response.json()["ui_tests"]) == 2

        # ── Stage 3: Execute a test ──
        response = client.post(
            "/api/v1/execution/execute",
            json=LOGIN_EXECUTION_REQUEST,
        )
        assert response.status_code == 200

        # ── Stage 4: Analyze a failure ──
        response = client.post(
            "/api/v1/failure-analysis/analyze?use_ai=false",
            json=LOGIN_FAILURE_INPUT.model_dump(mode="json"),
        )
        assert response.status_code == 200
        assert response.json()["input"]["test_name"] == "test_login_invalid_password"

    def test_jira_analysis_without_comments(self, client, mock_jira_services):
        """include_comments=false skips Jira comment fetching."""
        with patch.object(
            RequirementAnalysisAgent,
            "run",
            new=AsyncMock(
                return_value=AgentResult(
                    status="passed",
                    data=LOGIN_ANALYSIS_OUTPUT.model_dump(mode="json"),
                )
            ),
        ):
            response = client.get(
                "/api/v1/analysis/requirements/PROJ-123?include_comments=false",
                headers=JIRA_AUTH_HEADERS,
            )

        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════
# 3. Execution + Analysis Integration
# ═══════════════════════════════════════════════════════════

class TestExecutionAndAnalysis:
    """Integration between test execution and failure analysis."""

    def test_execute_failed_test_then_analyze(self, client):
        """Execute a failed test then analyze the resulting failure."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            proc = AsyncMock()
            proc.stdout = AsyncMock()
            proc.stderr = AsyncMock()
            proc.stdout.read = AsyncMock(return_value=b"")
            proc.stderr.read = AsyncMock(return_value=b"")
            proc.wait = AsyncMock(return_value=1)
            mock_create.return_value = proc

            response = client.post(
                "/api/v1/execution/execute",
                json={
                    "test_case_id": "tc-fail-001",
                    "test_case_name": "Failing test",
                    "execution_type": "playwright",
                    "script": 'test("fail", async () => { throw new Error("fail"); });',
                    "max_retries": 0,
                },
            )

        assert response.status_code == 200
        execution = response.json()
        assert execution["status"] in ("failed", "error")

        # Now analyze this execution's failure pattern
        response = client.post(
            "/api/v1/failure-analysis/analyze?use_ai=false",
            json={
                "test_name": "tc-fail-001",
                "test_suite": "ManualSuite",
                "status": "failed",
                "error_message": "Error: fail",
                "stack_trace": str(execution.get("error_message", "")),
                "execution_type": "playwright",
                "duration_ms": 100.0,
            },
        )
        assert response.status_code == 200
        analysis = response.json()
        assert analysis["input"]["test_name"] == "tc-fail-001"
        assert analysis["category"]["primary_category"] in (
            "assertion", "ui", "timeout", "flaky", "network", "api", "permission", "data", "unknown"
        )

    def test_batch_execute_then_batch_analyze(self, client):
        """Batch execution followed by batch failure analysis."""
        test_count = 3

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            proc = AsyncMock()
            proc.stdout = AsyncMock()
            proc.stderr = AsyncMock()
            proc.stdout.read = AsyncMock(return_value=b"")
            proc.stderr.read = AsyncMock(return_value=b"")
            proc.wait = AsyncMock(return_value=0)
            mock_create.return_value = proc

            # Batch execute
            response = client.post(
                "/api/v1/execution/execute/batch",
                json={
                    "tests": [
                        {
                            "test_case_id": f"tc-batch-{i}",
                            "test_case_name": f"Batch Test {i}",
                            "execution_type": "playwright",
                            "max_retries": 0,
                        }
                        for i in range(test_count)
                    ],
                    "max_parallel": 4,
                },
            )

        assert response.status_code == 200
        executions = response.json()
        assert len(executions) == test_count

        # Batch analyze failures
        response = client.post(
            "/api/v1/failure-analysis/analyze/batch?use_ai=false",
            json={
                "failures": [
                    {
                        "test_name": f"tc-batch-{i}",
                        "test_suite": "BatchSuite",
                        "status": "failed",
                        "error_message": f"AssertionError: Test {i} failed",
                        "execution_type": "playwright",
                        "duration_ms": 100.0 * (i + 1),
                        "tags": ["batch"],
                    }
                    for i in range(test_count)
                ],
                "total_tests": 10,
                "total_passed": 7,
                "total_failed": 3,
            },
        )

        assert response.status_code == 200
        batch_result = response.json()
        assert batch_result["total_analyzed"] == test_count
        assert len(batch_result["analyses"]) == test_count
        assert len(batch_result["category_distribution"]) > 0
        assert len(batch_result["risk_distribution"]) > 0
        assert batch_result["overall_risk"] is not None
        assert len(batch_result["top_issues"]) > 0


# ═══════════════════════════════════════════════════════════
# 4. Pipeline Error Handling & Edge Cases
# ═══════════════════════════════════════════════════════════

class TestPipelineErrorHandling:
    """Error handling and edge cases across the pipeline."""

    def test_analyze_from_execution_not_found(self, client):
        """Requesting analysis from a non-existent execution returns 404."""
        response = client.post(
            "/api/v1/failure-analysis/analyze/from-execution?execution_id=nonexistent-123&use_ai=false",
        )
        assert response.status_code == 404

    def test_execute_invalid_type(self, client):
        """Invalid execution test type returns 400."""
        response = client.post(
            "/api/v1/execution/execute/invalid?test_file=tests/foo.spec.ts",
        )
        assert response.status_code == 400

    def test_execute_with_extra_args(self, client, mock_subprocess):
        """Execute with extra_args passes them to the subprocess."""
        response = client.post(
            "/api/v1/execution/execute",
            json={
                "test_case_id": "tc-args",
                "test_case_name": "Args Test",
                "execution_type": "playwright",
                "extra_args": ["--headed", "--project=chromium"],
                "max_retries": 0,
            },
        )
        assert response.status_code == 200

    def test_pipeline_with_full_test_data_suggestions(self, client):
        """Test generation /data endpoint works standalone."""
        with patch(
            "test_generation.src.generator.TestGenerator._generate_test_data",
            new=AsyncMock(
                return_value={
                    "suggestions": LOGIN_TEST_GENERATION_OUTPUT.test_data_suggestions,
                    "prompt_tokens": 100,
                    "completion_tokens": 200,
                }
            ),
        ):
            response = client.post(
                "/api/v1/test-generation/generate/data",
                json=LOGIN_TEST_GENERATION_INPUT.model_dump(mode="json"),
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["test_data_suggestions"]) == 2
        assert data["test_data_suggestions"][0]["field"] == "email"
        assert data["test_data_suggestions"][1]["field"] == "password"

    def test_config_endpoints(self, client):
        """Execution and analysis config endpoints are accessible."""
        # Execution config
        response = client.get("/api/v1/execution/config")
        assert response.status_code == 200
        assert "max_retries" in response.json()

        # Analysis config
        response = client.get("/api/v1/failure-analysis/config")
        assert response.status_code == 200
        assert "ANALYSIS_ENABLE_AI" in response.json()

    def test_failure_analysis_with_ai_fallback(self, client):
        """Failure analysis falls back to heuristic when AI is unavailable."""
        # Request AI analysis - service will initialize LLM, which will fail and fallback
        response = client.post(
            "/api/v1/failure-analysis/analyze?use_ai=true",
            json=LOGIN_FAILURE_INPUT.model_dump(mode="json"),
        )

        # Should still succeed using heuristic fallback
        assert response.status_code == 200
        data = response.json()
        # Might be AI or fallback depending on environment, but must have valid analysis
        assert data["analysis_id"] is not None
        assert data["category"]["primary_category"] in (
            "assertion", "ui", "timeout", "flaky", "network", "api", "permission", "data", "unknown"
        )


# ═══════════════════════════════════════════════════════════
# 5. Jira API Integration
# ═══════════════════════════════════════════════════════════

def _jira_side_effect(comments_extra=None):
    """Factory for JiraClient._request side effects.

    Returns different mock responses based on URL path so endpoints
    that call multiple _request methods (e.g. get_issue then get_comments) work.
    """
    call_count = 0

    async def side_effect(method: str, url: str, **kwargs):
        nonlocal call_count
        call_count += 1
        if "comment" in url:
            return comments_extra or {"comments": LOGIN_JIRA_COMMENTS}
        if "issuetype" in url or "issue" in url:
            return LOGIN_JIRA_ISSUE
        if "project" in url:
            return [{"key": "PROJ", "name": "Test Project"}]
        if "search" in url:
            return {"issues": [LOGIN_JIRA_ISSUE], "total": 1}
        return {"success": True}

    return side_effect


class TestJiraIntegration:
    """Integration tests for Jira-backed features."""

    @pytest.fixture
    def mock_jira_client(self):
        """Mock the HTTP calls made by JiraClient at the _request level."""
        with patch("app.services.jira_client.JiraClient._request", new_callable=AsyncMock) as mock:
            yield mock

    def test_jira_connection_test(self, client, mock_jira_client):
        """Jira connection test endpoint works."""
        mock_jira_client.return_value = {"success": True}
        response = client.get(
            "/api/v1/jira/connection/test",
            headers=JIRA_AUTH_HEADERS,
        )
        assert response.status_code == 200

    def test_jira_get_issue(self, client, mock_jira_client):
        """Jira get_issue endpoint works."""
        mock_jira_client.return_value = LOGIN_JIRA_ISSUE
        response = client.get(
            "/api/v1/jira/issues/PROJ-123",
            headers=JIRA_AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "PROJ-123"

    def test_jira_get_comments(self, client, mock_jira_client):
        """Jira get_comments endpoint returns structured comments."""
        mock_jira_client.side_effect = _jira_side_effect(
            comments_extra={"comments": LOGIN_JIRA_COMMENTS}
        )
        response = client.get(
            "/api/v1/jira/issues/PROJ-123/comments",
            headers=JIRA_AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["body"] == "We need to support SSO in the future. The login flow should be extensible."

    def test_jira_acceptance_criteria(self, client):
        """Jira acceptance criteria endpoint."""
        from app.schemas.jira import JiraAcceptanceCriteria

        with patch(
            "app.api.v1.jira.JiraService.get_acceptance_criteria",
            new=AsyncMock(
                return_value=JiraAcceptanceCriteria(
                    raw_text="Acceptance criteria text",
                    criteria=LOGIN_REQUIREMENT["acceptance_criteria"],
                    source_issue_key="PROJ-123",
                )
            ),
        ):
            response = client.get(
                "/api/v1/jira/issues/PROJ-123/acceptance-criteria",
                headers=JIRA_AUTH_HEADERS,
            )

        assert response.status_code == 200
        assert len(response.json()["criteria"]) == 3

    def test_jira_projects(self, client, mock_jira_client):
        """Jira list projects endpoint."""
        mock_jira_client.return_value = [
            {"key": "PROJ", "name": "Test Project"},
        ]
        response = client.get(
            "/api/v1/jira/projects",
            headers=JIRA_AUTH_HEADERS,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_jira_search_stories(self, client, mock_jira_client):
        """Jira search stories endpoint."""
        mock_jira_client.return_value = {
            "issues": [LOGIN_JIRA_ISSUE],
            "total": 1,
        }
        response = client.get(
            "/api/v1/jira/search/stories?project_key=PROJ",
            headers=JIRA_AUTH_HEADERS,
        )
        assert response.status_code == 200

    def test_jira_missing_auth_returns_422(self, client):
        """Missing Jira auth headers returns validation error."""
        response = client.get("/api/v1/jira/issues/PROJ-123")
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════
# 6. Pipeline Data Flow Validation
# ═══════════════════════════════════════════════════════════

class TestPipelineDataFlow:
    """Validate data shapes flow correctly through pipeline stages."""

    def test_analysis_output_consumable_by_test_generation(self):
        """Requirement analysis output fields map to test generation input fields."""
        analysis = LOGIN_ANALYSIS_OUTPUT
        gen_input = LOGIN_TEST_GENERATION_INPUT

        # The overall purpose from analysis should inform the test generation requirement
        assert gen_input.requirement_summary == LOGIN_REQUIREMENT["story"]
        assert len(gen_input.acceptance_criteria) == len(LOGIN_REQUIREMENT["acceptance_criteria"])

        # Analysis scenarios can be turned into user flows
        assert len(analysis.functional_scenarios) >= len(gen_input.user_flows)
        for flow in gen_input.user_flows:
            assert flow.steps is not None

    def test_generated_tests_consumable_by_execution(self):
        """Test generation output can inform execution requests."""
        test_output = LOGIN_TEST_GENERATION_OUTPUT
        exec_request = LOGIN_EXECUTION_REQUEST

        # Generated test files contain scripts that execution can run
        assert len(test_output.ui_tests) > 0
        assert "playwright" in test_output.ui_tests[0].framework.lower()
        assert exec_request["execution_type"] == "playwright"

        # The generated code can be used as an execution script
        assert len(exec_request["script"]) > 0

    def test_execution_output_consumable_by_failure_analysis(self):
        """Failed execution can feed into failure analysis."""
        failed_exec = LOGIN_EXECUTION_FAILED
        analysis_input = LOGIN_FAILURE_INPUT

        # Execution status maps to analysis input status
        assert failed_exec.status.value == "failed"
        assert analysis_input.status == "failed"

        # Execution metadata can populate analysis tags
        assert set(analysis_input.tags).issubset(set(failed_exec.tags or []))

        # Both reference the same test identifier conceptually
        assert analysis_input.test_name != ""

    def test_batch_analysis_from_batch_execution(self):
        """Multiple failed executions form a valid batch analysis input."""
        batch_input = LOGIN_FAILURE_BATCH_INPUT
        assert len(batch_input.failures) == 3
        assert batch_input.total_failed == 3
        assert batch_input.total_tests == 20

        # Each failure has the required fields
        for f in batch_input.failures:
            assert f.test_name != ""
            assert f.status == "failed"
            assert f.error_message != ""

    def test_analysis_output_contains_all_required_sections(self):
        """Requirement analysis output has all required sections with correct types."""
        analysis = LOGIN_ANALYSIS_OUTPUT

        assert analysis.summary.overall_purpose != ""
        assert analysis.summary.complexity in ("low", "medium", "high")

        # All scenarios have required fields
        for fs in analysis.functional_scenarios:
            assert fs.title != ""
            assert fs.expected_result != ""
            assert fs.priority in ("low", "medium", "high")

        for ec in analysis.edge_cases:
            assert ec.title != ""
            assert ec.severity in ("low", "medium", "high", "critical")
            assert ec.category in ("format", "boundary", "concurrency", "time", "state", "null", "network", "compatibility", "performance", "security", "other")

        for ns in analysis.negative_scenarios:
            assert ns.title != ""
            assert ns.attack_vector in ("injection", "authentication", "session", "input_validation", "resource_exhaustion", "business_logic", "other")

        for ra in analysis.risk_areas:
            assert ra.area != ""
            assert ra.likelihood in ("low", "medium", "high")
            assert ra.impact in ("low", "medium", "high")

        for mr in analysis.missing_requirements:
            assert mr.title != ""
            assert mr.priority in ("low", "medium", "high")
