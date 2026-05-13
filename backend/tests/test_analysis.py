import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest

from app.analysis.models import (
    AnalysisInput,
    BatchAnalysisInput,
    FailureAnalysis,
    RootCauseSuggestion,
    FailureCategoryResult,
    RiskAssessment,
    RetryRecommendation,
    AnalysisSummary,
    FailureCategory,
    RiskLevel,
    BatchAnalysisResult,
)
from app.analysis.categorizer import FailureCategorizer
from app.analysis.risk_analyzer import RiskAnalyzer
from app.analysis.retry_advisor import RetryAdvisor
from app.analysis.summary_generator import SummaryGenerator
from app.analysis.screenshot_analyzer import ScreenshotAnalyzer
from app.analysis.config import analysis_settings


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def sample_assertion_input():
    return AnalysisInput(
        test_name="test_user_login",
        test_suite="LoginSuite",
        status="failed",
        error_message="AssertionError: Expected status 200, got 500",
        stack_trace='  File "tests/test_login.py", line 42, in test_user_login\n    assert response.status == 200',
        logs=["INFO: Starting login test", "ERROR: Response status: 500"],
        api_status_code=500,
        api_response='{"error": "Internal Server Error"}',
        execution_type="api",
        duration_ms=1500.0,
        tags=["smoke", "critical"],
    )


@pytest.fixture
def sample_timeout_input():
    return AnalysisInput(
        test_name="test_dashboard_loads",
        test_suite="DashboardSuite",
        status="failed",
        error_message="TimeoutError: locator.wait_for() timed out after 30000ms",
        stack_trace='  at #waitForSelector (/app/tests/dashboard.spec.ts:85)',
        logs=["Navigating to /dashboard", "Waiting for .dashboard-grid", "Timeout exceeded"],
        execution_type="playwright",
        duration_ms=30100.0,
        tags=["ui"],
    )


@pytest.fixture
def sample_network_input():
    return AnalysisInput(
        test_name="test_external_api",
        test_suite="IntegrationSuite",
        status="failed",
        error_message="FetchError: request to https://api.example.com/users failed, reason: ECONNREFUSED",
        logs=["Connecting to https://api.example.com", "ECONNREFUSED"],
        execution_type="api",
    )


# ── Test Models ───────────────────────────────────────────

class TestModels:
    def test_analysis_input_defaults(self):
        inp = AnalysisInput()
        assert inp.test_name == ""
        assert inp.status == "failed"
        assert inp.logs == []
        assert inp.tags == []
        assert inp.metadata == {}

    def test_failure_category_enum(self):
        assert FailureCategory.ASSERTION.value == "assertion"
        assert FailureCategory.TIMEOUT.value == "timeout"
        assert FailureCategory.FLAKY.value == "flaky"

    def test_risk_level_enum(self):
        assert RiskLevel.CRITICAL.value == "critical"
        assert RiskLevel.LOW.value == "low"

    def test_root_cause_suggestion_defaults(self):
        rc = RootCauseSuggestion()
        assert rc.title == ""
        assert rc.confidence == 0.0
        assert rc.evidence == []
        assert rc.suggested_fix is None

    def test_failure_category_result_defaults(self):
        fcr = FailureCategoryResult()
        assert fcr.primary_category == FailureCategory.UNKNOWN
        assert fcr.secondary_categories == []
        assert fcr.confidence == 0.0

    def test_risk_assessment_defaults(self):
        ra = RiskAssessment()
        assert ra.level == RiskLevel.LOW
        assert ra.score == 0.0
        assert ra.impacted_areas == []

    def test_retry_recommendation_defaults(self):
        rr = RetryRecommendation()
        assert rr.should_retry is False
        assert rr.suggested_max_retries == 1

    def test_analysis_summary_defaults(self):
        s = AnalysisSummary()
        assert s.one_liner == ""
        assert s.key_findings == []

    def test_failure_analysis_defaults(self):
        fa = FailureAnalysis()
        assert fa.analysis_id is not None
        assert fa.ai_used is False
        assert fa.ai_fallback is False

    def test_batch_analysis_input(self):
        batch = BatchAnalysisInput(
            failures=[AnalysisInput(test_name="t1"), AnalysisInput(test_name="t2")],
            total_tests=100,
            total_passed=80,
            total_failed=20,
        )
        assert len(batch.failures) == 2
        assert batch.total_tests == 100

    def test_batch_analysis_result(self):
        result = BatchAnalysisResult(total_analyzed=5, analysis_duration_ms=100.0)
        assert result.total_analyzed == 5


# ── Test FailureCategorizer ───────────────────────────────

class TestFailureCategorizer:
    def test_categorize_assertion(self, sample_assertion_input):
        categorizer = FailureCategorizer()
        result = categorizer.categorize(sample_assertion_input)
        assert result.primary_category == FailureCategory.ASSERTION
        assert result.confidence >= 0.8

    def test_categorize_timeout(self, sample_timeout_input):
        categorizer = FailureCategorizer()
        result = categorizer.categorize(sample_timeout_input)
        assert result.primary_category == FailureCategory.TIMEOUT
        assert result.confidence >= 0.8

    def test_categorize_network(self, sample_network_input):
        categorizer = FailureCategorizer()
        result = categorizer.categorize(sample_network_input)
        assert result.primary_category == FailureCategory.NETWORK
        assert result.confidence >= 0.8

    def test_categorize_api_status_code(self):
        inp = AnalysisInput(
            test_name="test_api",
            api_status_code=503,
            execution_type="api",
            error_message="Service Unavailable",
        )
        categorizer = FailureCategorizer()
        result = categorizer.categorize(inp)
        assert result.primary_category == FailureCategory.API
        assert "Server error" in result.reasoning or "503" in result.reasoning

    def test_categorize_permission(self):
        inp = AnalysisInput(
            test_name="test_auth",
            api_status_code=403,
            execution_type="api",
            error_message="Forbidden",
        )
        categorizer = FailureCategorizer()
        result = categorizer.categorize(inp)
        assert result.primary_category == FailureCategory.PERMISSION

    def test_categorize_ui_selector(self):
        inp = AnalysisInput(
            test_name="test_ui",
            execution_type="playwright",
            error_message="Can't find selector '.submit-btn'",
        )
        categorizer = FailureCategorizer()
        result = categorizer.categorize(inp)
        assert result.primary_category == FailureCategory.UI

    def test_categorize_unknown(self):
        inp = AnalysisInput(test_name="test_weird", error_message="Something odd happened")
        categorizer = FailureCategorizer()
        result = categorizer.categorize(inp)
        assert result.primary_category == FailureCategory.UNKNOWN
        assert result.confidence < 0.5

    def test_categorize_flaky_keyword(self):
        inp = AnalysisInput(
            test_name="test_flaky",
            error_message="This test is flaky and randomly fails",
        )
        categorizer = FailureCategorizer()
        result = categorizer.categorize(inp)
        assert result.primary_category == FailureCategory.FLAKY

    def test_requires_ai(self):
        categorizer = FailureCategorizer()
        low_conf = FailureCategoryResult(
            primary_category=FailureCategory.DATA, confidence=0.5
        )
        assert categorizer.requires_ai(low_conf) is True

        high_conf = FailureCategoryResult(
            primary_category=FailureCategory.ASSERTION, confidence=0.85
        )
        assert categorizer.requires_ai(high_conf) is False

    def test_merge_ai_result(self):
        categorizer = FailureCategorizer()
        pattern = FailureCategoryResult(
            primary_category=FailureCategory.ASSERTION, confidence=0.85
        )
        ai = FailureCategoryResult(
            primary_category=FailureCategory.ASSERTION, confidence=0.9
        )
        merged = categorizer.merge_ai_result(pattern, ai)
        assert merged.primary_category == FailureCategory.ASSERTION

        low_pattern = FailureCategoryResult(
            primary_category=FailureCategory.UNKNOWN, confidence=0.4
        )
        ai_better = FailureCategoryResult(
            primary_category=FailureCategory.DATA, confidence=0.8
        )
        merged2 = categorizer.merge_ai_result(low_pattern, ai_better)
        assert merged2.primary_category == FailureCategory.DATA


# ── Test RiskAnalyzer ─────────────────────────────────────

class TestRiskAnalyzer:
    def test_analyze_assertion_medium(self, sample_assertion_input):
        analyzer = RiskAnalyzer()
        category = FailureCategoryResult(
            primary_category=FailureCategory.ASSERTION, confidence=0.9
        )
        risk = analyzer.analyze(sample_assertion_input, category)
        assert risk.level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
        assert risk.score > 0

    def test_analyze_permission_critical(self):
        analyzer = RiskAnalyzer()
        inp = AnalysisInput(
            test_name="test",
            tags=["critical"],
            error_message="Authentication failed",
        )
        category = FailureCategoryResult(
            primary_category=FailureCategory.PERMISSION, confidence=0.9
        )
        risk = analyzer.analyze(inp, category)
        assert risk.level == RiskLevel.CRITICAL

    def test_analyze_flaky_low(self):
        analyzer = RiskAnalyzer()
        inp = AnalysisInput(test_name="test")
        category = FailureCategoryResult(
            primary_category=FailureCategory.FLAKY, confidence=0.8
        )
        risk = analyzer.analyze(inp, category)
        assert risk.level == RiskLevel.LOW

    def test_risk_modifiers_from_tags(self):
        analyzer = RiskAnalyzer()
        inp = AnalysisInput(test_name="test", tags=["p0", "critical"])
        category = FailureCategoryResult(
            primary_category=FailureCategory.ASSERTION, confidence=0.9
        )
        risk = analyzer.analyze(inp, category)
        # Medium base + 0.2 from tags = 0.6 which is HIGH
        assert risk.score >= 0.6

    def test_risk_modifiers_from_retries(self):
        analyzer = RiskAnalyzer()
        inp = AnalysisInput(test_name="test", retry_count=5)
        category = FailureCategoryResult(
            primary_category=FailureCategory.ASSERTION, confidence=0.9
        )
        risk = analyzer.analyze(inp, category)
        # Medium base(0.4) + 0.1 from retries > 2 = 0.5
        assert risk.score >= 0.5

    def test_aggregate_risk_empty(self):
        assert RiskAnalyzer.aggregate_risk([]).level == RiskLevel.LOW

    def test_aggregate_risk(self):
        assessments = [
            RiskAssessment(level=RiskLevel.LOW, score=0.15),
            RiskAssessment(level=RiskLevel.HIGH, score=0.7),
        ]
        aggregated = RiskAnalyzer.aggregate_risk(assessments)
        assert aggregated.level == RiskLevel.HIGH
        assert aggregated.score == 0.7


# ── Test RetryAdvisor ─────────────────────────────────────

class TestRetryAdvisor:
    def test_non_retryable_assertion(self, sample_assertion_input):
        advisor = RetryAdvisor()
        cat = FailureCategoryResult(primary_category=FailureCategory.ASSERTION)
        rec = advisor.recommend(sample_assertion_input, cat)
        assert rec.should_retry is False

    def test_non_retryable_permission(self):
        advisor = RetryAdvisor()
        inp = AnalysisInput(test_name="test")
        cat = FailureCategoryResult(primary_category=FailureCategory.PERMISSION)
        rec = advisor.recommend(inp, cat)
        assert rec.should_retry is False

    def test_always_retry_flaky(self):
        advisor = RetryAdvisor()
        inp = AnalysisInput(test_name="test")
        cat = FailureCategoryResult(primary_category=FailureCategory.FLAKY)
        rec = advisor.recommend(inp, cat)
        assert rec.should_retry is True
        assert rec.suggested_max_retries >= 1

    def test_always_retry_timeout(self, sample_timeout_input):
        advisor = RetryAdvisor()
        cat = FailureCategoryResult(primary_category=FailureCategory.TIMEOUT)
        rec = advisor.recommend(sample_timeout_input, cat)
        assert rec.should_retry is True
        assert rec.suggested_delay_seconds >= 5.0

    def test_always_retry_network(self, sample_network_input):
        advisor = RetryAdvisor()
        cat = FailureCategoryResult(primary_category=FailureCategory.NETWORK)
        rec = advisor.recommend(sample_network_input, cat)
        assert rec.should_retry is True

    def test_retry_exhausted(self):
        advisor = RetryAdvisor()
        inp = AnalysisInput(test_name="test", retry_count=5)
        cat = FailureCategoryResult(primary_category=FailureCategory.FLAKY)
        rec = advisor.recommend(inp, cat)
        assert rec.should_retry is False

    def test_conditional_retry_ui_server_error(self):
        advisor = RetryAdvisor()
        inp = AnalysisInput(
            test_name="test",
            api_status_code=502,
            error_message="Bad Gateway",
        )
        cat = FailureCategoryResult(primary_category=FailureCategory.UI)
        rec = advisor.recommend(inp, cat)
        assert rec.should_retry is True

    def test_conditional_retry_ui_no_indicator(self):
        advisor = RetryAdvisor()
        inp = AnalysisInput(test_name="test")
        cat = FailureCategoryResult(primary_category=FailureCategory.UI)
        rec = advisor.recommend(inp, cat)
        assert rec.should_retry is False


# ── Test SummaryGenerator ─────────────────────────────────

class TestSummaryGenerator:
    def test_generate_one_liner(self, sample_assertion_input):
        root_cause = RootCauseSuggestion(
            title="Server returned 500",
            description="The API returned 500 instead of 200",
            confidence=0.9,
        )
        category = FailureCategoryResult(
            primary_category=FailureCategory.ASSERTION, confidence=0.85
        )
        risk = RiskAssessment(level=RiskLevel.HIGH, score=0.7)
        retry = RetryRecommendation(should_retry=False)

        summary = SummaryGenerator.generate(
            sample_assertion_input, root_cause, category, risk, retry
        )
        assert "ASSERTION" in summary.one_liner
        assert "Server returned 500" in summary.one_liner
        assert len(summary.key_findings) > 0
        assert len(summary.recommended_actions) > 0

    def test_generate_retry_recommendation(self, sample_timeout_input):
        root_cause = RootCauseSuggestion(
            title="Dashboard load timeout",
            description="Page took too long to load",
        )
        category = FailureCategoryResult(
            primary_category=FailureCategory.TIMEOUT, confidence=0.9
        )
        risk = RiskAssessment(level=RiskLevel.MEDIUM, score=0.4)
        retry = RetryRecommendation(
            should_retry=True,
            suggested_max_retries=2,
            suggested_delay_seconds=5.0,
        )

        summary = SummaryGenerator.generate(
            sample_timeout_input, root_cause, category, risk, retry
        )
        assert any("Retry" in a for a in summary.recommended_actions)

    def test_generate_critical_escalation(self):
        inp = AnalysisInput(test_name="test_critical")
        root_cause = RootCauseSuggestion(title="Security breach")
        category = FailureCategoryResult(
            primary_category=FailureCategory.PERMISSION, confidence=0.9
        )
        risk = RiskAssessment(level=RiskLevel.CRITICAL, score=0.95)
        retry = RetryRecommendation(should_retry=False)

        summary = SummaryGenerator.generate(
            inp, root_cause, category, risk, retry
        )
        assert any("Escalate" in a for a in summary.recommended_actions)


# ── Test ScreenshotAnalyzer ───────────────────────────────

class TestScreenshotAnalyzer:
    @pytest.mark.asyncio
    async def test_no_screenshot(self):
        analyzer = ScreenshotAnalyzer()
        inp = AnalysisInput(test_name="test")
        result = await analyzer.analyze(inp)
        assert result is None

    @pytest.mark.asyncio
    async def test_screenshot_not_found(self, tmp_path):
        analyzer = ScreenshotAnalyzer()
        inp = AnalysisInput(
            test_name="test",
            screenshot_path=str(tmp_path / "nonexistent.png"),
        )
        result = await analyzer.analyze(inp)
        assert result is None


# ── Test ResultAnalyzer ───────────────────────────────────

class TestResultAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_without_ai(self, sample_assertion_input):
        from app.analysis.result_analyzer import ResultAnalyzer

        analyzer = ResultAnalyzer(ai_client=None)
        result = await analyzer.analyze(sample_assertion_input, use_ai=False)

        assert result.ai_used is False
        assert result.analysis_id is not None
        assert result.category.primary_category == FailureCategory.ASSERTION
        assert result.risk.level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
        assert result.retry.should_retry is False
        assert result.summary.one_liner != ""
        assert result.duration_ms is not None

    @pytest.mark.asyncio
    async def test_analyze_timeout_without_ai(self, sample_timeout_input):
        from app.analysis.result_analyzer import ResultAnalyzer

        analyzer = ResultAnalyzer(ai_client=None)
        result = await analyzer.analyze(sample_timeout_input, use_ai=False)

        assert result.category.primary_category == FailureCategory.TIMEOUT
        assert result.retry.should_retry is True
        assert result.summary.one_liner != ""

    @pytest.mark.asyncio
    async def test_analyze_with_ai(self, sample_assertion_input):
        from app.analysis.result_analyzer import ResultAnalyzer

        analyzer = ResultAnalyzer(ai_client=MagicMock())

        async def mock_ai_method(*args, **kwargs):
            return RootCauseSuggestion(
                title="Server Error",
                description="API returned 500",
                confidence=0.9,
                evidence=["Status code 500"],
                suggested_fix="Fix server endpoint",
            )

        analyzer._analyze_root_cause_ai = mock_ai_method
        analyzer._analyze_category_ai = AsyncMock(return_value=None)
        analyzer._analyze_risk_ai = AsyncMock(
            return_value=RiskAssessment(level=RiskLevel.HIGH, score=0.7)
        )
        analyzer._analyze_retry_ai = AsyncMock(
            return_value=RetryRecommendation(should_retry=False)
        )
        analyzer._analyze_summary_ai = AsyncMock(
            return_value=AnalysisSummary(one_liner="Test failed due to server error")
        )

        result = await analyzer.analyze(sample_assertion_input, use_ai=True)

        assert result.ai_used is True
        assert result.root_cause.title == "Server Error"
        assert result.root_cause.suggested_fix == "Fix server endpoint"

    @pytest.mark.asyncio
    async def test_analyze_with_ai_fallback(self, sample_assertion_input):
        mock_ai = AsyncMock()
        mock_ai.generate = AsyncMock(side_effect=RuntimeError("API down"))

        from app.analysis.result_analyzer import ResultAnalyzer

        analyzer = ResultAnalyzer(ai_client=mock_ai)
        result = await analyzer.analyze(sample_assertion_input, use_ai=True)

        assert result.ai_used is False
        assert result.ai_fallback is True
        assert result.category.primary_category == FailureCategory.ASSERTION

    @pytest.mark.asyncio
    async def test_analyze_batch(self):
        from app.analysis.result_analyzer import ResultAnalyzer

        analyzer = ResultAnalyzer(ai_client=None)
        batch = BatchAnalysisInput(
            failures=[
                AnalysisInput(
                    test_name="test1",
                    error_message="AssertionError: Expected 200 got 500",
                ),
                AnalysisInput(
                    test_name="test2",
                    error_message="TimeoutError: Timed out",
                ),
                AnalysisInput(
                    test_name="test3",
                    error_message="ECONNREFUSED",
                ),
            ]
        )

        result = await analyzer.analyze_batch(batch, use_ai=False)
        assert result.total_analyzed == 3
        assert len(result.analyses) == 3
        assert len(result.category_distribution) > 0
        assert len(result.risk_distribution) > 0
        assert result.overall_risk is not None
        assert len(result.top_issues) > 0

    @pytest.mark.asyncio
    async def test_parse_ai_json_valid(self):
        from app.analysis.result_analyzer import ResultAnalyzer

        content = '{"title": "Test", "confidence": 0.8}'
        raw = ResultAnalyzer._parse_ai_json(content)
        assert raw == {"title": "Test", "confidence": 0.8}

    @pytest.mark.asyncio
    async def test_parse_ai_json_embedded(self):
        from app.analysis.result_analyzer import ResultAnalyzer

        content = "Here's the result:\n\n```json\n{\"title\": \"Test\"}\n```"
        raw = ResultAnalyzer._parse_ai_json(content)
        assert raw == {"title": "Test"}

    @pytest.mark.asyncio
    async def test_parse_ai_json_invalid(self):
        from app.analysis.result_analyzer import ResultAnalyzer

        content = "Not JSON at all"
        raw = ResultAnalyzer._parse_ai_json(content)
        assert raw is None

    def test_truncate(self):
        from app.analysis.result_analyzer import ResultAnalyzer

        assert ResultAnalyzer._truncate("hello", 10) == "hello"
        assert ResultAnalyzer._truncate("hello world", 5) == "hello..."
        assert ResultAnalyzer._truncate(None, 10) is None


# ── Test AnalysisService ──────────────────────────────────

class TestAnalysisService:
    @pytest.mark.asyncio
    async def test_analyze_failure(self, sample_assertion_input):
        from app.analysis.service import AnalysisService

        service = AnalysisService(ai_client=None)
        result = await service.analyze_failure(sample_assertion_input, use_ai=False)

        assert isinstance(result, FailureAnalysis)
        assert result.category.primary_category == FailureCategory.ASSERTION

    @pytest.mark.asyncio
    async def test_analyze_batch(self):
        from app.analysis.service import AnalysisService

        service = AnalysisService(ai_client=None)
        batch = BatchAnalysisInput(
            failures=[
                AnalysisInput(test_name="t1", error_message="Failed"),
                AnalysisInput(test_name="t2", error_message="Error"),
            ]
        )
        result = await service.analyze_batch(batch, use_ai=False)
        assert result.total_analyzed == 2


# ── Test API Endpoints ────────────────────────────────────

class TestAnalysisAPI:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_analyze_endpoint_no_ai(self, client, sample_assertion_input):
        payload = sample_assertion_input.model_dump(mode="json")
        response = client.post(
            "/api/v1/failure-analysis/analyze?use_ai=false",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["category"]["primary_category"] == "assertion"
        assert data["ai_used"] is False
        assert data["summary"]["one_liner"] != ""

    def test_analyze_batch_endpoint(self, client):
        payload = {
            "failures": [
                {
                    "test_name": "test_1",
                    "error_message": "AssertionError: Failed",
                    "execution_type": "api",
                },
                {
                    "test_name": "test_2",
                    "error_message": "TimeoutError",
                    "execution_type": "playwright",
                },
            ],
        }
        response = client.post(
            "/api/v1/failure-analysis/analyze/batch?use_ai=false",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_analyzed"] == 2
        assert len(data["analyses"]) == 2
        assert len(data["category_distribution"]) > 0

    def test_analyze_from_execution_not_found(self, client):
        response = client.post(
            "/api/v1/failure-analysis/analyze/from-execution?execution_id=nonexistent&use_ai=false",
        )
        assert response.status_code == 404

    def test_get_config_endpoint(self, client):
        response = client.get("/api/v1/failure-analysis/config")
        assert response.status_code == 200
        data = response.json()
        assert "ANALYSIS_ENABLE_AI" in data

    def test_analyze_with_full_data(self, client):
        payload = {
            "test_name": "full_test",
            "test_suite": "FullSuite",
            "status": "failed",
            "error_message": "AssertionError: Expected true, got false",
            "stack_trace": '  File "test.py", line 10, in test\n    assert True == False',
            "logs": ["Step 1", "Step 2", "FAILED"],
            "api_status_code": 422,
            "execution_type": "api",
            "duration_ms": 500.0,
            "retry_count": 2,
            "tags": ["regression"],
        }
        response = client.post(
            "/api/v1/failure-analysis/analyze?use_ai=false",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["input"]["test_name"] == "full_test"
        assert data["category"]["primary_category"] in ("assertion", "api")
        assert data["summary"]["one_liner"] != ""
