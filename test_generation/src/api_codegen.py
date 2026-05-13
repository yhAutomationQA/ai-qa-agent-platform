from __future__ import annotations

import json
import structlog
from typing import Any

from .models import GeneratedTestFile, TestGenerationInput
from .utils import clean_code_block, format_ts_code, sanitize_filename

logger = structlog.get_logger()

API_TEST_TEMPLATE = """import {{ test, expect }} from "@playwright/test";
import {{ ApiClient }} from "@api/ApiClient";
import {{ getUser }} from "@data/users";

const BASE_URL = process.env.API_URL || "http://localhost:8000/api/v1";

{endpoint_tests}
"""

ENDPOINT_TEST_TEMPLATE = """test.describe("{method} {path}", () => {{
{positive_tests}
{negative_tests}
}});
"""


class ApiCodeGenerator:
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    def generate_all(self, scenarios: list[dict[str, Any]]) -> list[GeneratedTestFile]:
        """Generate API test files from structured scenario descriptions."""
        files: list[GeneratedTestFile] = []
        endpoint_groups: dict[str, list[dict[str, Any]]] = {}

        for scenario in scenarios:
            endpoint = scenario.get("endpoint", "/unknown")
            if endpoint not in endpoint_groups:
                endpoint_groups[endpoint] = []
            endpoint_groups[endpoint].append(scenario)

        endpoint_blocks = []
        for endpoint, group in endpoint_groups.items():
            first = group[0]
            method = first.get("method", "GET")
            path = first.get("path", endpoint)

            block = self._generate_endpoint_block(method, path, group)
            endpoint_blocks.append(block)

        code = API_TEST_TEMPLATE.format(endpoint_tests="\n\n".join(endpoint_blocks))

        files.append(
            GeneratedTestFile(
                filename="tests/api/api-tests.spec.ts",
                code=format_ts_code(code),
                description="Auto-generated API test suite",
            )
        )

        logger.info("api_test_files_generated", count=len(files), scenarios=len(scenarios))
        return files

    def generate_from_llm_output(
        self,
        input_data: TestGenerationInput,
        llm_output: dict[str, Any],
    ) -> list[GeneratedTestFile]:
        """Parse LLM JSON output into API test files."""
        files: list[GeneratedTestFile] = []
        safe_name = sanitize_filename(input_data.requirement_summary[:50])

        scenarios_raw = llm_output.get("scenarios", llm_output.get("endpoints", []))
        if isinstance(scenarios_raw, str):
            try:
                scenarios_raw = json.loads(clean_code_block(scenarios_raw))
            except json.JSONDecodeError:
                logger.warning("failed_to_parse_llm_api_output")
                return files

        if isinstance(scenarios_raw, list):
            return self.generate_all(scenarios_raw)

        raw_code = llm_output.get("code", "")
        if raw_code:
            cleaned = clean_code_block(raw_code)
            formatted = format_ts_code(cleaned)
            files.append(
                GeneratedTestFile(
                    filename=f"tests/api/{safe_name}.api.spec.ts",
                    code=formatted,
                    description=f"API tests for: {input_data.requirement_summary[:80]}",
                )
            )

        return files

    def _generate_endpoint_block(
        self,
        method: str,
        path: str,
        scenarios: list[dict[str, Any]],
    ) -> str:
        positive_tests = []
        negative_tests = []

        for scenario in scenarios:
            for tc in scenario.get("tests", []):
                name = tc.get("name", "should respond correctly")
                test_type = tc.get("type", "positive")
                expected_status = tc.get("expected_status", 200)
                auth = tc.get("auth_required", False)
                request_data = tc.get("request", {})
                body = request_data.get("body", {})
                assertions = tc.get("assertions", [])

                test_lines = [f'  test("{name}", async ({{ request }}) => {{']
                if auth:
                    test_lines.append('    const admin = getUser("admin");')
                    test_lines.append(
                        f'    const res = await request.{method.lower()}(`${{BASE_URL}}{path}`, {{'
                    )
                else:
                    test_lines.append(
                        f'    const res = await request.{method.lower()}(`${{BASE_URL}}{path}`, {{'
                    )

                if body:
                    body_str = json.dumps(body, indent=6)
                    test_lines.append(f"      data: {body_str},")

                test_lines.append("    });")
                test_lines.append(f"    expect(res.status()).toBe({expected_status});")
                for assertion in assertions:
                    test_lines.append(f"    // TODO: {assertion}")
                test_lines.append("  });")

                if test_type in ("positive",):
                    positive_tests.extend(test_lines)
                else:
                    negative_tests.extend(test_lines)

        positive_block = (
            "\n  // ── Positive Tests ──\n" + "\n\n".join(positive_tests)
            if positive_tests
            else ""
        )
        negative_block = (
            "\n  // ── Negative Tests ──\n" + "\n\n".join(negative_tests)
            if negative_tests
            else ""
        )

        return ENDPOINT_TEST_TEMPLATE.format(
            method=method,
            path=path,
            positive_tests=positive_block,
            negative_tests=negative_block,
        )
