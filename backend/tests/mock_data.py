"""Comprehensive mock data for all pipeline stages.

Usage in tests:
    from tests.mock_data import (
        LOGIN_REQUIREMENT,
        MOCK_ANALYSIS_OUTPUT,
        MOCK_TEST_GENERATION_INPUT,
        ...
    )
"""

from datetime import datetime, timezone

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
)
from app.execution.models import (
    TestExecution,
    ExecutionType,
    ExecutionStatus,
    ExecutionSummary,
)
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
from test_generation.src.models import (
    TestGenerationInput,
    TestGenerationOutput,
    GeneratedTestFile,
    TestDataSuggestion,
    UserFlow,
    UserFlowStep,
    TestType,
    Framework,
)


# ═══════════════════════════════════════════════════════════
# 1. Requirement Analysis
# ═══════════════════════════════════════════════════════════

LOGIN_REQUIREMENT = {
    "story": "User should login using email and password",
    "acceptance_criteria": [
        "User can login with valid credentials",
        "Error shown for invalid password",
        "Remember me should persist session",
    ],
}

LOGIN_REQUIREMENT_TASK = {
    "issue_key": "MANUAL",
    "summary": LOGIN_REQUIREMENT["story"],
    "description": "As a user, I want to log in with my email and password so that I can access my account securely.",
    "acceptance_criteria": LOGIN_REQUIREMENT["acceptance_criteria"],
    "comments": [],
    "labels": ["auth", "frontend"],
    "priority": "high",
}

LOGIN_ANALYSIS_OUTPUT = RequirementAnalysisOutput(
    summary=RequirementSummary(
        overall_purpose="Enable user authentication via email and password login",
        complexity="medium",
        key_functionality=[
            "Authenticate user with email and password",
            "Validate credentials against stored user data",
            "Display error messages for invalid credentials",
            "Persist session when Remember Me is checked",
        ],
        stakeholders=["End Users", "Platform Administrators"],
        dependencies=["User database", "Session store", "Authentication service"],
    ),
    functional_scenarios=[
        FunctionalScenario(
            id="FS-01",
            title="Successful login with valid credentials",
            description="User enters correct email and password and clicks login",
            preconditions=["User is registered", "User is on login page"],
            steps=[
                "Enter registered email in email field",
                "Enter correct password in password field",
                "Click Login button",
            ],
            expected_result="User is redirected to dashboard with active session",
            relates_to_ac="User can login with valid credentials",
            priority="high",
        ),
        FunctionalScenario(
            id="FS-02",
            title="Login with invalid password shows error",
            description="User enters correct email but wrong password",
            preconditions=["User is registered", "User is on login page"],
            steps=[
                "Enter registered email",
                "Enter incorrect password",
                "Click Login button",
            ],
            expected_result="Error message 'Invalid password' is displayed, user stays on login page",
            relates_to_ac="Error shown for invalid password",
            priority="high",
        ),
        FunctionalScenario(
            id="FS-03",
            title="Remember Me persists session across browser restart",
            description="User checks Remember Me, logs in, closes browser, and returns",
            preconditions=["User is registered"],
            steps=[
                "Enter valid credentials",
                "Check Remember Me checkbox",
                "Click Login",
                "Close and reopen browser",
                "Navigate to dashboard URL",
            ],
            expected_result="User is still authenticated without re-entering credentials",
            relates_to_ac="Remember me should persist session",
            priority="medium",
        ),
        FunctionalScenario(
            id="FS-04",
            title="Login with unregistered email shows appropriate error",
            description="User enters email that does not exist in the system",
            preconditions=["User is on login page"],
            steps=[
                "Enter unregistered email address",
                "Enter any password",
                "Click Login button",
            ],
            expected_result="Error message shown: 'No account found with this email'",
            relates_to_ac="Error shown for invalid password",
            priority="medium",
        ),
    ],
    edge_cases=[
        EdgeCase(
            id="EC-01",
            title="Email with leading/trailing whitespace",
            description="Email input is not trimmed before validation",
            input_condition="' user@example.com ' (with spaces)",
            expected_behavior="System trims whitespace and processes login normally, or rejects with clear format error",
            severity="medium",
            category="format",
        ),
        EdgeCase(
            id="EC-02",
            title="Maximum length email and password",
            description="User submits credentials at the maximum allowed length",
            input_condition="254-character email + 128-character password",
            expected_behavior="Credentials are accepted if valid, or rejected with length-specific error",
            severity="low",
            category="boundary",
        ),
        EdgeCase(
            id="EC-03",
            title="Concurrent login from multiple devices",
            description="Same user logs in from two different browsers simultaneously",
            input_condition="Two simultaneous login requests with same credentials",
            expected_behavior="Both sessions are created; or second one invalidates the first, based on session policy",
            severity="medium",
            category="concurrency",
        ),
    ],
    negative_scenarios=[
        NegativeScenario(
            id="NS-01",
            title="SQL injection in email field",
            description="Attacker attempts SQL injection via the email input",
            malicious_input="' OR '1'='1' --",
            expected_failure="System rejects the input or safely escapes it; no SQL error is exposed",
            attack_vector="injection",
            severity="critical",
        ),
        NegativeScenario(
            id="NS-02",
            title="Brute force login attempts",
            description="Attacker rapidly tries multiple password combinations",
            malicious_input="Repeated POST requests with different passwords in short succession",
            expected_failure="Account is temporarily locked or rate-limited after N failed attempts",
            attack_vector="resource_exhaustion",
            severity="high",
        ),
        NegativeScenario(
            id="NS-03",
            title="XSS in password field",
            description="Attacker injects JavaScript via the password field",
            malicious_input="<script>alert('xss')</script>",
            expected_failure="Input is sanitized/encoded; no script execution occurs",
            attack_vector="input_validation",
            severity="high",
        ),
    ],
    risk_areas=[
        RiskArea(
            area="Authentication bypass",
            description="Vulnerability in login logic could allow unauthorized access",
            likelihood="low",
            impact="high",
            mitigation="Server-side validation, rate limiting, proper session management",
        ),
        RiskArea(
            area="Credential leakage",
            description="Passwords could be exposed in logs, URLs, or error messages",
            likelihood="medium",
            impact="high",
            mitigation="Never log passwords, use POST method, return generic error messages",
        ),
    ],
    missing_requirements=[
        MissingRequirement(
            title="Password reset flow",
            description="No mechanism for users who forgot their password",
            rationale="Users frequently forget passwords; without reset flow they are locked out permanently",
            suggested_action="Add 'Forgot Password' link that triggers email-based reset flow",
            priority="high",
        ),
        MissingRequirement(
            title="Account lockout policy",
            description="No specification for what happens after multiple failed attempts",
            rationale="Without lockout, brute force attacks are possible",
            suggested_action="Define max failed attempts before temporary lockout",
            priority="medium",
        ),
    ],
    metadata=AnalysisMetadata(
        model_used="gpt-4o",
        total_tokens=850,
        processing_time_ms=3200.0,
        source_issue_key="MANUAL",
        analyzed_at=datetime.now(timezone.utc),
    ),
)


# ═══════════════════════════════════════════════════════════
# 2. Test Generation
# ═══════════════════════════════════════════════════════════

LOGIN_TEST_GENERATION_INPUT = TestGenerationInput(
    requirement_summary=LOGIN_REQUIREMENT["story"],
    acceptance_criteria=LOGIN_REQUIREMENT["acceptance_criteria"],
    user_flows=[
        UserFlow(
            name="Successful login",
            description="User logs in with valid email and password",
            steps=[
                UserFlowStep(action="Enter email", selector="#email", value="user@example.com"),
                UserFlowStep(action="Enter password", selector="#password", value="validPass123"),
                UserFlowStep(action="Click Login", selector="#login-btn"),
            ],
            expected_outcomes=["User redirected to dashboard"],
        ),
        UserFlow(
            name="Failed login",
            description="User enters incorrect password",
            steps=[
                UserFlowStep(action="Enter email", selector="#email", value="user@example.com"),
                UserFlowStep(action="Enter password", selector="#password", value="wrongPassword"),
                UserFlowStep(action="Click Login", selector="#login-btn"),
            ],
            expected_outcomes=["Error message displayed", "User stays on login page"],
        ),
    ],
    technology_stack=Framework.NEXTJS,
    test_types=[TestType.UI, TestType.API],
    additional_context="Login page is at /login, dashboard is at /dashboard",
)

LOGIN_TEST_GENERATION_OUTPUT = TestGenerationOutput(
    ui_tests=[
        GeneratedTestFile(
            filename="tests/auth/login.spec.ts",
            language="typescript",
            framework="playwright",
            code='import { test, expect } from "@playwright/test";\n\ntest("should login with valid credentials", async ({ page }) => {\n  await page.goto("/login");\n  await page.fill("#email", "user@example.com");\n  await page.fill("#password", "validPass123");\n  await page.click("#login-btn");\n  await expect(page).toHaveURL("/dashboard");\n});\n',
            description="UI test for successful login flow",
        ),
        GeneratedTestFile(
            filename="tests/auth/login-error.spec.ts",
            language="typescript",
            framework="playwright",
            code='import { test, expect } from "@playwright/test";\n\ntest("should show error on invalid password", async ({ page }) => {\n  await page.goto("/login");\n  await page.fill("#email", "user@example.com");\n  await page.fill("#password", "wrongPassword");\n  await page.click("#login-btn");\n  await expect(page.locator(".error-message")).toBeVisible();\n});\n',
            description="UI test for invalid password error display",
        ),
    ],
    api_tests=[
        GeneratedTestFile(
            filename="tests/auth/login.api.spec.ts",
            language="typescript",
            framework="playwright",
            code='import { test, expect } from "@playwright/test";\n\ntest.describe("POST /api/auth/login", () => {\n  test("returns 200 with valid credentials", async ({ request }) => {\n    const res = await request.post("/api/auth/login", {\n      data: { email: "user@example.com", password: "validPass123" },\n    });\n    expect(res.status()).toBe(200);\n  });\n\n  test("returns 401 with invalid password", async ({ request }) => {\n    const res = await request.post("/api/auth/login", {\n      data: { email: "user@example.com", password: "wrongPassword" },\n    });\n    expect(res.status()).toBe(401);\n  });\n});\n',
            description="API tests for login endpoint",
        ),
    ],
    test_data_suggestions=[
        TestDataSuggestion(
            field="email",
            data_type="email",
            valid_values=["user@example.com", "test.user@domain.co.uk"],
            invalid_values=["", "not-an-email", "@missing.com"],
            edge_values=["a@b.co", "user+tag@example.com"],
            description="Email field validation strategies",
        ),
        TestDataSuggestion(
            field="password",
            data_type="password",
            valid_values=["P@ssw0rd!", "Str0ng!Pass#2024"],
            invalid_values=["", "short", "           "],
            edge_values=["a" * 128, "Unicode密码!@#$%"],
            description="Password field validation and complexity checks",
        ),
    ],
    summary="Generated 2 UI test files, 1 API test file, 2 data suggestions for: User should login using email and password",
    prompt_tokens=450,
    completion_tokens=1200,
    model_used="gpt-4o",
)


# ═══════════════════════════════════════════════════════════
# 3. Test Execution
# ═══════════════════════════════════════════════════════════

LOGIN_EXECUTION_REQUEST = {
    "test_case_id": "tc-login-001",
    "test_case_name": "Login with valid credentials",
    "execution_type": "playwright",
    "script": 'test("login", async ({ page }) => {\n  await page.goto("/login");\n  await page.fill("#email", "user@example.com");\n  await page.fill("#password", "validPass123");\n  await page.click("#login-btn");\n  await expect(page).toHaveURL("/dashboard");\n});',
    "parameters": {"url": "https://example.com", "timeout": 30000},
    "tags": ["smoke", "auth", "critical"],
    "max_retries": 2,
}

LOGIN_EXECUTION = TestExecution(
    id="exec-login-001",
    test_case_id="tc-login-001",
    test_case_name="Login with valid credentials",
    execution_type=ExecutionType.PLAYWRIGHT,
    status=ExecutionStatus.PASSED,
    attempt=1,
    max_retries=2,
    script=LOGIN_EXECUTION_REQUEST["script"],
    parameters={"url": "https://example.com", "timeout": 30000},
    tags=["smoke", "auth", "critical"],
    started_at=datetime.now(timezone.utc),
    completed_at=datetime.now(timezone.utc),
    duration_ms=3250.0,
    summary=ExecutionSummary(
        total_tests=3,
        passed=3,
        failed=0,
        total_duration_ms=3250.0,
        retries_used=0,
        max_retries=2,
    ),
)

LOGIN_EXECUTION_FAILED = TestExecution(
    id="exec-login-fail-001",
    test_case_id="tc-login-002",
    test_case_name="Login with invalid password",
    execution_type=ExecutionType.PLAYWRIGHT,
    status=ExecutionStatus.FAILED,
    attempt=1,
    max_retries=2,
    tags=["smoke", "auth"],
    summary=ExecutionSummary(
        total_tests=1,
        passed=0,
        failed=1,
        total_duration_ms=1200.0,
        retries_used=0,
        max_retries=2,
    ),
)


# ═══════════════════════════════════════════════════════════
# 4. Failure Analysis
# ═══════════════════════════════════════════════════════════

LOGIN_FAILURE_INPUT = AnalysisInput(
    test_name="test_login_invalid_password",
    test_suite="AuthSuite",
    status="failed",
    error_message="AssertionError: Expected error message to be visible, but element .error-message was not found",
    stack_trace='  at AuthPage.login (/app/tests/auth/login.spec.ts:25)\n  at Context.<anonymous> (/app/tests/auth/login.spec.ts:42)',
    logs=[
        "INFO: Navigating to /login",
        "INFO: Filling email field",
        "INFO: Filling password field",
        "INFO: Clicking login button",
        "ERROR: AssertionError: Expected error message to be visible",
    ],
    api_status_code=None,
    api_response=None,
    execution_type="playwright",
    duration_ms=1200.0,
    retry_count=1,
    tags=["smoke", "auth"],
    metadata={"browser": "chromium", "viewport": "1280x720"},
)

LOGIN_FAILURE_BATCH_INPUT = BatchAnalysisInput(
    failures=[
        LOGIN_FAILURE_INPUT,
        AnalysisInput(
            test_name="test_login_timeout",
            test_suite="AuthSuite",
            status="failed",
            error_message="TimeoutError: page.waitForSelector() timed out after 30000ms",
            logs=["Navigating to /login", "Waiting for #email selector", "Timeout exceeded"],
            execution_type="playwright",
            duration_ms=30100.0,
            tags=["ui"],
        ),
        AnalysisInput(
            test_name="test_login_api_500",
            test_suite="AuthAPI",
            status="failed",
            error_message="HTTPError: 500 Internal Server Error",
            api_status_code=500,
            api_response='{"error": "Internal server error"}',
            execution_type="api",
            duration_ms=800.0,
            tags=["api"],
        ),
    ],
    run_id="run-auth-suite-001",
    total_tests=20,
    total_passed=17,
    total_failed=3,
    total_skipped=0,
)

LOGIN_FAILURE_ANALYSIS = FailureAnalysis(
    analysis_id="analysis-login-001",
    input=LOGIN_FAILURE_INPUT,
    root_cause=RootCauseSuggestion(
        title="Error message element not rendered on failed login",
        description="The test expects an .error-message element to appear after submitting invalid credentials, "
        "but the element was not found in the DOM. This could mean the frontend does not render the error "
        "message, or the selector is incorrect.",
        confidence=0.85,
        evidence=[
            "Step 'Click login button' completed successfully",
            "No error message element found after submission",
            "Backend returned 401 as expected (no API error)",
        ],
        suggested_fix="Verify that the error message component is rendered on 401 responses. "
        "Check if the error selector matches the actual DOM structure.",
    ),
    category=FailureCategoryResult(
        primary_category=FailureCategory.UI,
        secondary_categories=[FailureCategory.ASSERTION],
        confidence=0.82,
        reasoning="The failure is UI-related: the expected DOM element was not found. "
        "The underlying cause could be a missing frontend state.",
    ),
    risk=RiskAssessment(
        level=RiskLevel.HIGH,
        score=0.72,
        impacted_areas=["Authentication flow", "User experience"],
        blast_radius="All users attempting login with invalid credentials",
        reasoning="Login failure affects all users and blocks a critical path. "
        "Error feedback is essential for user experience.",
    ),
    retry=RetryRecommendation(
        should_retry=True,
        confidence=0.65,
        reason="UI assertion failures may be transient due to rendering timing",
        suggested_max_retries=2,
        suggested_delay_seconds=3.0,
        conditions=["Add waitForSelector with increased timeout before asserting"],
    ),
    summary=AnalysisSummary(
        one_liner="Login error message element not rendered after invalid credentials submission",
        detailed_summary="The test submitted invalid login credentials and expected an error message to appear. "
        "The backend correctly rejected the request (401), but the frontend did not display the error element. "
        "This is likely a frontend rendering issue or a selector mismatch.",
        key_findings=[
            "Backend authentication is working correctly (returned 401)",
            "Frontend error message element is missing from DOM",
            "No JavaScript console errors detected",
        ],
        recommended_actions=[
            "Inspect the frontend component that handles login errors",
            "Verify the error element uses the expected CSS class .error-message",
            "Add an explicit wait for the error element with a generous timeout",
        ],
        severity=RiskLevel.HIGH,
    ),
    ai_used=False,
    ai_fallback=False,
    analyzed_at=datetime.now(timezone.utc),
    duration_ms=45.0,
)


# ═══════════════════════════════════════════════════════════
# 5. Jira Mock Data
# ═══════════════════════════════════════════════════════════

JIRA_AUTH_HEADERS = {
    "X-Jira-Url": "https://test.atlassian.net",
    "X-Jira-Email": "test@example.com",
    "X-Jira-Token": "fake-api-token",
}

LOGIN_JIRA_ISSUE = {
    "id": "100",
    "key": "PROJ-123",
    "fields": {
        "summary": LOGIN_REQUIREMENT["story"],
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "As a user, I want to log in with my email and password."}
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Acceptance Criteria:"}
                    ],
                },
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": "User can login with valid credentials"}
                                    ],
                                }
                            ],
                        },
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": "Error shown for invalid password"}
                                    ],
                                }
                            ],
                        },
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": "Remember me should persist session"}
                                    ],
                                }
                            ],
                        },
                    ],
                },
            ],
        },
        "issuetype": {"name": "Story"},
        "priority": {"name": "High"},
        "status": {"name": "In Progress", "statusCategory": {"name": "In Progress"}},
        "labels": ["auth", "frontend"],
        "assignee": {"displayName": "John Doe", "emailAddress": "john@example.com"},
        "reporter": {"displayName": "Jane Smith", "emailAddress": "jane@example.com"},
        "created": "2025-01-15T10:00:00.000+0000",
    },
}

LOGIN_JIRA_COMMENTS = [
    {
        "id": "101",
        "author": {"displayName": "Alice", "emailAddress": "alice@example.com"},
        "body": "We need to support SSO in the future. The login flow should be extensible.",
        "created": "2025-01-16T14:30:00.000+0000",
    },
    {
        "id": "102",
        "author": {"displayName": "Bob", "emailAddress": "bob@example.com"},
        "body": "Make sure to hash passwords with bcrypt. No plaintext storage.",
        "created": "2025-01-17T09:15:00.000+0000",
    },
]


# ═══════════════════════════════════════════════════════════
# 6. Mock Fixture Dictionary (for parametrized tests)
# ═══════════════════════════════════════════════════════════

ALL_MOCK_DATA = {
    "requirement": LOGIN_REQUIREMENT,
    "analysis_output": LOGIN_ANALYSIS_OUTPUT,
    "test_generation_input": LOGIN_TEST_GENERATION_INPUT,
    "test_generation_output": LOGIN_TEST_GENERATION_OUTPUT,
    "execution_request": LOGIN_EXECUTION_REQUEST,
    "execution_passed": LOGIN_EXECUTION,
    "execution_failed": LOGIN_EXECUTION_FAILED,
    "failure_input": LOGIN_FAILURE_INPUT,
    "failure_batch_input": LOGIN_FAILURE_BATCH_INPUT,
    "failure_analysis": LOGIN_FAILURE_ANALYSIS,
    "jira_issue": LOGIN_JIRA_ISSUE,
    "jira_comments": LOGIN_JIRA_COMMENTS,
}
