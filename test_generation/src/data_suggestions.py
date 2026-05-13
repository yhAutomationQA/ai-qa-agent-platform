from __future__ import annotations

import json
import structlog
from typing import Any

from .models import TestDataSuggestion, TestGenerationInput
from .utils import clean_code_block

logger = structlog.get_logger()

COMMON_TEST_DATA: dict[str, list[dict[str, Any]]] = {
    "email": [
        {
            "field": "email",
            "data_type": "email",
            "valid_values": [
                "user@example.com",
                "user.name@example.co.uk",
                "user+tag@example.com",
                "user@sub.example.com",
            ],
            "invalid_values": [
                "",
                "not-an-email",
                "@missing-username.com",
                "spaces in@email.com",
                "user@.com",
            ],
            "edge_values": [
                "a@b.co",
                "very.long.email.address.that.might.exceed.maximum.length.limit@example.com",
                "!#$%&'*+-/=?^_`{|}~@example.com",
            ],
            "description": "Email fields require valid format, length limits, and proper domain validation",
        }
    ],
    "password": [
        {
            "field": "password",
            "data_type": "password",
            "valid_values": [
                "P@ssw0rd123!",
                "Str0ng!Pass#2024",
                "MyP@ssw0rd!WithLotsOfCharacters123",
            ],
            "invalid_values": [
                "",
                "short",
                "nouppercaseornumbers",
                "NOSPECIALCHARS123",
                "           ",
            ],
            "edge_values": [
                "a" * 128,
                "P@1" * 30,
                "Unicode密码!@#$%^&*()",
            ],
            "description": "Passwords need complexity (upper, lower, digit, special), length checks, and should not accept common patterns",
        }
    ],
    "text": [
        {
            "field": "name",
            "data_type": "text",
            "valid_values": [
                "John Doe",
                "Alice Smith-Watson",
                "José García",
            ],
            "invalid_values": [
                "",
                "   ",
                "<script>alert(1)</script>",
                "' OR '1'='1",
            ],
            "edge_values": [
                "a" * 255,
                "a" * 1000,
                "Line1\nLine2\nLine3",
                "  leading and trailing spaces  ",
            ],
            "description": "Text fields need XSS prevention, SQL injection protection, length limits, and whitespace handling",
        }
    ],
    "number": [
        {
            "field": "age",
            "data_type": "number",
            "valid_values": ["25", "0", "999999"],
            "invalid_values": [
                "",
                "abc",
                "-1",
                "3.14",
                "null",
            ],
            "edge_values": [
                "0",
                "2147483647",
                "-2147483648",
                "1e309",
            ],
            "description": "Numeric fields need type validation, range checks, and boundary testing",
        }
    ],
}


class DataSuggestionEngine:
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    def suggest_for_input(
        self,
        input_data: TestGenerationInput,
    ) -> list[TestDataSuggestion]:
        """Generate test data suggestions based on input analysis."""
        suggestions: list[TestDataSuggestion] = []
        keywords_seen: set[str] = set()

        text = f"{input_data.requirement_summary} {' '.join(input_data.acceptance_criteria)}".lower()
        if input_data.additional_context:
            text += f" {input_data.additional_context}".lower()

        keyword_mapping = {
            "email": "email",
            "mail": "email",
            "password": "password",
            "pass": "password",
            "name": "text",
            "username": "text",
            "address": "text",
            "description": "text",
            "comment": "text",
            "age": "number",
            "count": "number",
            "amount": "number",
            "price": "number",
            "quantity": "number",
            "limit": "number",
        }

        for keyword, field_type in keyword_mapping.items():
            if keyword in text and field_type not in keywords_seen:
                keywords_seen.add(field_type)
                templates = COMMON_TEST_DATA.get(field_type, [])
                for tpl in templates:
                    suggestions.append(TestDataSuggestion(**tpl))

        for flow in input_data.user_flows:
            for step in flow.steps:
                if step.selector and "input" in step.selector.lower():
                    field_name = step.selector.split('"')[1] if '"' in step.selector else step.selector
                    suggestions.append(
                        TestDataSuggestion(
                            field=field_name,
                            data_type="text",
                            valid_values=["Sample value", "Test data"],
                            invalid_values=["", "<script>"],
                            edge_values=["a" * 256, ""],
                            description=f"Field found in user flow: {field_name}",
                        )
                    )

        if not suggestions:
            suggestions.append(
                TestDataSuggestion(
                    field="general",
                    data_type="text",
                    valid_values=["Default valid value"],
                    invalid_values=["", "   "],
                    edge_values=["a" * 1000],
                    description="General test data suggestion for this feature",
                )
            )

        logger.info("data_suggestions_generated", count=len(suggestions))
        return suggestions

    def parse_llm_suggestions(
        self,
        input_data: TestGenerationInput,
        llm_output: dict[str, Any],
    ) -> list[TestDataSuggestion]:
        """Parse LLM output into structured test data suggestions."""
        suggestions: list[TestDataSuggestion] = []

        raw = llm_output.get("suggestions", llm_output.get("data", []))
        if isinstance(raw, str):
            try:
                raw = json.loads(clean_code_block(raw))
            except json.JSONDecodeError:
                logger.warning("failed_to_parse_llm_data_output")
                return self.suggest_for_input(input_data)

        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    suggestions.append(
                        TestDataSuggestion(
                            field=item.get("field", "unknown"),
                            data_type=item.get("data_type", "text"),
                            valid_values=item.get("valid_values", []),
                            invalid_values=item.get("invalid_values", []),
                            edge_values=item.get("edge_values", []),
                            description=item.get("description", ""),
                        )
                    )

        if not suggestions:
            return self.suggest_for_input(input_data)

        logger.info("llm_data_suggestions_parsed", count=len(suggestions))
        return suggestions
