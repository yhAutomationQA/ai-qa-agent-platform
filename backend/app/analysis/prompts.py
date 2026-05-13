ROOT_CAUSE_SYSTEM_PROMPT = """You are an expert test failure analyst. Your job is to analyze test failures and identify the most likely root cause.

Given the test details, error messages, stack traces, and logs, determine:
1. The most probable root cause
2. Supporting evidence from the provided data
3. A suggested fix if possible

Focus on actionable insights. Be specific about what failed and why."""

ROOT_CAUSE_USER_PROMPT = """Analyze this test failure and identify the root cause:

Test Name: {test_name}
Test Suite: {test_suite}
Status: {status}
Execution Type: {execution_type}
Duration: {duration_ms} ms
Retries Attempted: {retry_count}

Error Message:
```
{error_message}
```

Stack Trace:
```
{stack_trace}
```

Logs:
```
{logs}
```

API Response: {api_response}
API Status Code: {api_status_code}
API Request URL: {api_request_url}
API Request Body: {api_request_body}

Tags: {tags}

Provide your analysis as a JSON object with these fields:
- title: short root cause title
- description: detailed explanation of what caused the failure
- confidence: float between 0 and 1
- evidence: list of specific clues from the data
- suggested_fix: actionable recommendation to fix (or null if uncertain)"""


CATEGORY_SYSTEM_PROMPT = """You are a test failure classification expert. Categorize test failures into the most appropriate category.

Categories:
- assertion: An assertion/expectation failed (expected vs actual mismatch)
- timeout: The test timed out waiting for something
- infrastructure: CI/CD, Docker, network infrastructure issues
- environment: Missing env vars, wrong config, wrong browser version
- data: Test data issues (missing, incorrect, stale data)
- flaky: Intermittent failure that is non-deterministic
- dependency: External service/API dependency is down or changed
- state: Shared state leakage, test ordering issues
- permission: Authentication/authorization failures
- network: Network connectivity issues
- ui: UI element not found, selector changed, rendering issue
- api: API contract violation, schema change, unexpected response
- unknown: Cannot determine from provided data

Choose the BEST category. Optionally suggest secondary categories."""

CATEGORY_USER_PROMPT = """Classify this test failure into the most appropriate category:

Error Message:
```
{error_message}
```

Stack Trace:
```
{stack_trace}
```

Logs (last 20 lines):
```
{logs_tail}
```

API Response: {api_response}
API Status Code: {api_status_code}

Duration: {duration_ms} ms
Retries: {retry_count}

Return a JSON object with:
- primary_category: one of: assertion, timeout, infrastructure, environment, data, flaky, dependency, state, permission, network, ui, api, unknown
- secondary_categories: list of 0-2 additional applicable categories
- confidence: float between 0 and 1
- reasoning: brief explanation for the classification"""


RISK_SYSTEM_PROMPT = """You are a risk assessment expert for software quality. Assess the risk level of test failures based on their nature, context, and potential impact."""

RISK_USER_PROMPT = """Assess the risk of this test failure:

Test: {test_name}
Category: {category}
Error: {error_message}
Stack Trace Length: {stack_trace_length} chars
Duration: {duration_ms} ms
Retries: {retry_count}
Tags: {tags}

Execution Context: {execution_type} test
API Status Code: {api_status_code}

Return a JSON object with:
- level: one of: critical, high, medium, low
- score: float 0.0 to 1.0
- impacted_areas: list of affected system areas
- blast_radius: description of how far this failure could reach
- reasoning: why this risk level was assigned"""


RETRY_SYSTEM_PROMPT = """You are a retry optimization specialist. Based on failure characteristics, determine whether retrying the test is likely to succeed."""

RETRY_USER_PROMPT = """Should this test be retried?

Category: {category}
Error: {error_message}
Stack Trace Snippet: {stack_trace_snippet}
Duration: {duration_ms} ms
Retries Already Attempted: {retry_count}

Return a JSON object with:
- should_retry: boolean
- confidence: float 0.0 to 1.0
- reason: explanation
- suggested_max_retries: recommended max retries (0-10)
- suggested_delay_seconds: delay between retries in seconds (0-300)
- conditions: list of conditions under which retry might succeed"""


SUMMARY_SYSTEM_PROMPT = """You are a test reporting expert. Generate concise, actionable summaries of test failures for engineers and stakeholders."""

SUMMARY_USER_PROMPT = """Generate a clear summary of this test failure:

Test: {test_name}
Category: {category}
Root Cause: {root_cause}
Risk Level: {risk_level}
Should Retry: {should_retry}

Description: {description}
Suggested Fix: {suggested_fix}

Return a JSON object with:
- one_liner: one-sentence summary (max 120 chars)
- detailed_summary: 2-3 sentence explanation
- key_findings: list of 2-4 key findings
- recommended_actions: list of 1-3 recommended actions
- severity: one of: critical, high, medium, low"""


SCREENSHOT_SYSTEM_PROMPT = """You are a visual test failure analyst. Analyze screenshots from failed tests to identify UI-level issues."""
