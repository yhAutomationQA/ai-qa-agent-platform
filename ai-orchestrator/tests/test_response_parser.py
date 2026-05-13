import pytest

from ai_orchestrator.parsing.parser import ResponseParser
from ai_orchestrator.exceptions import InvalidResponseError


class TestResponseParser:
    def test_parse_json_basic(self):
        result = ResponseParser.parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_with_code_block(self):
        text = '```json\n{"key": "value"}\n```'
        result = ResponseParser.parse_json(text)
        assert result == {"key": "value"}

    def test_parse_json_with_code_block_no_lang(self):
        text = '```\n[1, 2, 3]\n```'
        result = ResponseParser.parse_json(text)
        assert result == [1, 2, 3]

    def test_parse_json_array_in_text(self):
        text = "Here is the result:\n[{\"id\": 1}, {\"id\": 2}]"
        result = ResponseParser.parse_json(text)
        assert result == [{"id": 1}, {"id": 2}]

    def test_parse_json_invalid_raises(self):
        with pytest.raises(InvalidResponseError):
            ResponseParser.parse_json("not json at all")

    def test_parse_test_scenarios(self):
        text = """[
            {
                "title": "Valid login",
                "description": "Test login with valid credentials",
                "preconditions": ["User exists"],
                "steps": ["Enter username", "Enter password", "Click login"],
                "expected_results": ["User is redirected to dashboard"],
                "tags": ["smoke"],
                "priority": "high",
                "category": "functional"
            }
        ]"""
        scenarios = ResponseParser.parse_test_scenarios(text)
        assert len(scenarios) == 1
        assert scenarios[0].title == "Valid login"
        assert scenarios[0].priority == "high"
        assert len(scenarios[0].steps) == 3

    def test_parse_test_scenarios_from_object(self):
        text = '{"scenarios": [{"title": "Test A", "steps": [], "expected_results": []}]}'
        scenarios = ResponseParser.parse_test_scenarios(text)
        assert len(scenarios) == 1
        assert scenarios[0].title == "Test A"

    def test_parse_edge_cases(self):
        text = """[
            {
                "title": "Empty input",
                "description": "Submit with empty fields",
                "input_condition": "All fields empty",
                "expected_behavior": "Show validation errors",
                "severity": "high",
                "category": "empty/null"
            }
        ]"""
        cases = ResponseParser.parse_edge_cases(text)
        assert len(cases) == 1
        assert cases[0].title == "Empty input"
        assert cases[0].severity == "high"

    def test_parse_edge_cases_empty_raises(self):
        with pytest.raises(InvalidResponseError):
            ResponseParser.parse_edge_cases("[]")

    def test_parse_negative_scenarios(self):
        text = """[
            {
                "title": "SQL Injection",
                "description": "Inject SQL in username field",
                "malicious_input": "' OR '1'='1",
                "expected_failure": "Request rejected with 400",
                "attack_vector": "injection",
                "severity": "critical"
            }
        ]"""
        scenarios = ResponseParser.parse_negative_scenarios(text)
        assert len(scenarios) == 1
        assert scenarios[0].attack_vector == "injection"
        assert scenarios[0].severity == "critical"

    def test_parse_requirement_summary(self):
        text = """{"summary": "A login system", "key_points": ["point1"], "stakeholders": ["dev"], "dependencies": [], "risk_areas": [], "estimated_effort": "medium"}"""
        result = ResponseParser.parse_requirement_summary(text)
        assert result["summary"] == "A login system"
        assert len(result["key_points"]) == 1

    def test_parse_requirement_summary_missing_keys(self):
        with pytest.raises(InvalidResponseError):
            ResponseParser.parse_requirement_summary('{"summary": "test"}')
