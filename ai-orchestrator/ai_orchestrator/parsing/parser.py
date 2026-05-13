import json
import re
import structlog
from typing import Any

from ai_orchestrator.models import TestScenario, EdgeCase, NegativeScenario
from ai_orchestrator.exceptions import InvalidResponseError

logger = structlog.get_logger()


class ResponseParser:
    @staticmethod
    def parse_json(text: str) -> Any:
        cleaned = ResponseParser._extract_json(text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise InvalidResponseError(text, f"Invalid JSON: {e}")

    @staticmethod
    def parse_test_scenarios(text: str) -> list[TestScenario]:
        data = ResponseParser.parse_json(text)
        if isinstance(data, dict):
            data = data.get("scenarios", data.get("test_cases", [data]))
        if not isinstance(data, list):
            data = [data]

        scenarios = []
        for item in data:
            scenario = TestScenario(
                id=item.get("id", ""),
                title=item.get("title", item.get("name", "Untitled")),
                description=item.get("description", ""),
                preconditions=item.get("preconditions", []),
                steps=item.get("steps", []),
                expected_results=item.get("expected_results", item.get("expectedResults", [])),
                test_data=item.get("test_data", item.get("testData", {})),
                tags=item.get("tags", []),
                priority=item.get("priority", "medium"),
                category=item.get("category", "functional"),
            )
            scenarios.append(scenario)

        if not scenarios:
            raise InvalidResponseError(text, "No test scenarios found in response")

        logger.info("parsed_test_scenarios", count=len(scenarios))
        return scenarios

    @staticmethod
    def parse_edge_cases(text: str) -> list[EdgeCase]:
        data = ResponseParser.parse_json(text)
        if isinstance(data, dict):
            data = data.get("edge_cases", data.get("cases", [data]))
        if not isinstance(data, list):
            data = [data]

        cases = []
        for item in data:
            cases.append(
                EdgeCase(
                    title=item.get("title", "Untitled"),
                    description=item.get("description", ""),
                    input_condition=item.get("input_condition", item.get("inputCondition", "")),
                    expected_behavior=item.get("expected_behavior", item.get("expectedBehavior", "")),
                    severity=item.get("severity", "medium"),
                    category=item.get("category", "boundary"),
                )
            )

        if not cases:
            raise InvalidResponseError(text, "No edge cases found in response")

        logger.info("parsed_edge_cases", count=len(cases))
        return cases

    @staticmethod
    def parse_negative_scenarios(text: str) -> list[NegativeScenario]:
        data = ResponseParser.parse_json(text)
        if isinstance(data, dict):
            data = data.get("negative_scenarios", data.get("scenarios", [data]))
        if not isinstance(data, list):
            data = [data]

        scenarios = []
        for item in data:
            scenarios.append(
                NegativeScenario(
                    title=item.get("title", "Untitled"),
                    description=item.get("description", ""),
                    malicious_input=item.get("malicious_input", item.get("maliciousInput", "")),
                    expected_failure=item.get("expected_failure", item.get("expectedFailure", "")),
                    attack_vector=item.get("attack_vector", item.get("attackVector", "input_validation")),
                    severity=item.get("severity", "medium"),
                )
            )

        if not scenarios:
            raise InvalidResponseError(text, "No negative scenarios found in response")

        logger.info("parsed_negative_scenarios", count=len(scenarios))
        return scenarios

    @staticmethod
    def parse_requirement_summary(text: str) -> dict:
        data = ResponseParser.parse_json(text)
        required_keys = ["summary", "key_points"]
        for key in required_keys:
            if key not in data:
                raise InvalidResponseError(text, f"Missing required key: '{key}'")
        logger.info("parsed_requirement_summary")
        return data

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()

        code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()

        for pattern in [r"(\{[\s\S]*\})", r"(\[[\s\S]*\])"]:
            match = re.search(pattern, text)
            if match:
                candidate = match.group(1)
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    continue

        raise InvalidResponseError(text, "No valid JSON found")
