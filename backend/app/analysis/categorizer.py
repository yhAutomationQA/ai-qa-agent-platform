import re
from typing import Any

from app.analysis.models import (
    FailureCategory,
    FailureCategoryResult,
    AnalysisInput,
)


class FailureCategorizer:
    PATTERN_RULES: list[tuple[re.Pattern, FailureCategory, str]] = [
        (re.compile(r"AssertionError|assert .* failed|expected .* to equal|expect\(.*\)\.toBe"), FailureCategory.ASSERTION, "Assertion failure"),
        (re.compile(r"TimeoutError|timed? ?out|Timeout \d+ms exceeded"), FailureCategory.TIMEOUT, "Operation timed out"),
        (re.compile(r"ECONNREFUSED|ECONNRESET|ETIMEDOUT|ENOTFOUND|socket hang up"), FailureCategory.NETWORK, "Network connection error"),
        (re.compile(r"5\d{2}|Internal Server Error|Service Unavailable|Bad Gateway"), FailureCategory.API, "Server error response"),
        (re.compile(r"\b(401|403)\b|Unauthorized|Forbidden"), FailureCategory.PERMISSION, "Permission/authentication error"),
        (re.compile(r"4\d{2}|Not Found"), FailureCategory.API, "Client error response"),
        (re.compile(r"ENOENT|EACCES|EISDIR|Module not found|Cannot find module"), FailureCategory.INFRASTRUCTURE, "File/system error"),
        (re.compile(r"Can't find selector|No element found|locator\(\)|not visible|element not interactable"), FailureCategory.UI, "UI element not found"),
        (re.compile(r"404|Not Found"), FailureCategory.API, "Resource not found"),
        (re.compile(r"flaky|intermittent|randomly|sometimes|unstable"), FailureCategory.FLAKY, "Pattern matches flaky indicator"),
    ]

    AI_CATEGORIZABLE: set[FailureCategory] = {
        FailureCategory.DATA,
        FailureCategory.ENVIRONMENT,
        FailureCategory.STATE,
        FailureCategory.DEPENDENCY,
        FailureCategory.PERMISSION,
        FailureCategory.UNKNOWN,
    }

    def categorize(self, input_data: AnalysisInput) -> FailureCategoryResult:
        combined = self._build_pattern_input(input_data)
        matched = self._match_patterns(combined)

        if matched:
            return matched

        return self._infer_from_context(input_data)

    def _build_pattern_input(self, input_data: AnalysisInput) -> str:
        parts = [
            input_data.error_message or "",
            input_data.stack_trace or "",
            "\n".join(input_data.logs[-20:]),
            input_data.api_response or "",
            str(input_data.api_status_code or ""),
        ]
        return "\n".join(parts)

    def _match_patterns(self, text: str) -> FailureCategoryResult | None:
        best_match: tuple[int, FailureCategory, str] | None = None

        for pattern, category, reasoning in self.PATTERN_RULES:
            match = pattern.search(text)
            if match:
                priority = self._category_priority(category)
                if best_match is None or priority < best_match[0]:
                    best_match = (priority, category, f"{reasoning}: '{match.group()[:80]}'")

        if best_match:
            _, category, reasoning = best_match
            return FailureCategoryResult(
                primary_category=category,
                confidence=0.85,
                reasoning=reasoning,
            )

        return None

    def _infer_from_context(self, input_data: AnalysisInput) -> FailureCategoryResult:
        if input_data.execution_type == "api" and input_data.api_status_code:
            if input_data.api_status_code >= 500:
                return FailureCategoryResult(
                    primary_category=FailureCategory.API,
                    confidence=0.7,
                    reasoning=f"API returned {input_data.api_status_code}",
                )
            if input_data.api_status_code in (403, 401):
                return FailureCategoryResult(
                    primary_category=FailureCategory.PERMISSION,
                    confidence=0.75,
                    reasoning=f"API returned {input_data.api_status_code}",
                )

        if input_data.execution_type == "playwright" and input_data.error_message:
            if "selector" in input_data.error_message.lower():
                return FailureCategoryResult(
                    primary_category=FailureCategory.UI,
                    confidence=0.6,
                    reasoning="Selector-related error in UI test",
                )

        return FailureCategoryResult(
            primary_category=FailureCategory.UNKNOWN,
            confidence=0.4,
            reasoning="Could not determine category from available data",
        )

    @staticmethod
    def _category_priority(category: FailureCategory) -> int:
        ordering = {
            FailureCategory.ASSERTION: 1,
            FailureCategory.TIMEOUT: 2,
            FailureCategory.INFRASTRUCTURE: 3,
            FailureCategory.ENVIRONMENT: 4,
            FailureCategory.NETWORK: 5,
            FailureCategory.API: 6,
            FailureCategory.UI: 7,
            FailureCategory.DATA: 8,
            FailureCategory.STATE: 9,
            FailureCategory.DEPENDENCY: 10,
            FailureCategory.PERMISSION: 4,
            FailureCategory.FLAKY: 12,
            FailureCategory.UNKNOWN: 13,
        }
        return ordering.get(category, 99)

    def requires_ai(self, result: FailureCategoryResult) -> bool:
        return result.primary_category in self.AI_CATEGORIZABLE and result.confidence < 0.7

    def merge_ai_result(
        self,
        pattern_result: FailureCategoryResult,
        ai_result: FailureCategoryResult | None,
    ) -> FailureCategoryResult:
        if ai_result is None:
            return pattern_result
        if pattern_result.confidence >= 0.85:
            return pattern_result
        return ai_result
