import pytest
from test_generation.src.utils import (
    clean_code_block,
    format_ts_code,
    sanitize_filename,
    build_context_block,
)
from test_generation.src.models import TestGenerationInput


class TestCleanCodeBlock:
    def test_no_fence(self):
        assert clean_code_block("hello") == "hello"

    def test_with_typescript_fence(self):
        raw = "```typescript\nconst x = 1;\n```"
        assert clean_code_block(raw) == "const x = 1;"

    def test_with_unlabeled_fence(self):
        raw = "```\nconst x = 1;\n```"
        assert clean_code_block(raw) == "const x = 1;"

    def test_strips_markdown_surrounding(self):
        raw = "Some text\n```ts\ncode here\n```\nMore text"
        assert clean_code_block(raw) == "code here"


class TestFormatTsCode:
    def test_removes_excessive_blank_lines(self):
        code = "line1\n\n\n\n\nline2"
        result = format_ts_code(code)
        assert result == "line1\n\nline2"

    def test_preserves_single_blank_lines(self):
        code = "line1\n\nline2"
        assert format_ts_code(code) == "line1\n\nline2"


class TestSanitizeFilename:
    def test_basic(self):
        assert sanitize_filename("Login Feature") == "login-feature"

    def test_special_chars(self):
        assert sanitize_filename("User @#$ Profile") == "user-profile"

    def test_empty(self):
        assert sanitize_filename("") == "test"


class TestBuildContextBlock:
    def test_minimal_input(self):
        inp = TestGenerationInput(requirement_summary="Test feature")
        result = build_context_block(inp)
        assert "Test feature" in result
        assert "## Requirement Summary" in result

    def test_with_acceptance_criteria(self):
        inp = TestGenerationInput(
            requirement_summary="Login",
            acceptance_criteria=["Must have email", "Must have password"],
        )
        result = build_context_block(inp)
        assert "Must have email" in result

    def test_with_user_flows(self):
        from test_generation.src.models import UserFlow, UserFlowStep

        inp = TestGenerationInput(
            requirement_summary="Search",
            user_flows=[
                UserFlow(
                    name="Basic search",
                    steps=[UserFlowStep(action="Type query")],
                    expected_outcomes=["Results shown"],
                )
            ],
        )
        result = build_context_block(inp)
        assert "Basic search" in result
        assert "Type query" in result
