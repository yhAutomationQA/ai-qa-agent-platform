import pytest
from test_generation.src.models import (
    TestGenerationInput,
    TestGenerationOutput,
    UserFlow,
    UserFlowStep,
    GeneratedTestFile,
    TestDataSuggestion,
    TestType,
    Framework,
)


class TestTestGenerationInput:
    def test_minimal_input(self):
        inp = TestGenerationInput(requirement_summary="Login feature")
        assert inp.requirement_summary == "Login feature"
        assert inp.acceptance_criteria == []
        assert inp.user_flows == []
        assert inp.technology_stack == Framework.NEXTJS
        assert inp.test_types == [TestType.UI, TestType.API]
        assert inp.has_acceptance_criteria is False
        assert inp.has_user_flows is False

    def test_full_input(self):
        inp = TestGenerationInput(
            requirement_summary="User registration",
            acceptance_criteria=["Email is required", "Password must be 8+ chars"],
            user_flows=[
                UserFlow(
                    name="Sign up",
                    steps=[UserFlowStep(action="Enter email", selector="#email")],
                    expected_outcomes=["User is registered"],
                )
            ],
            technology_stack=Framework.REACT,
            test_types=[TestType.API],
        )
        assert inp.has_acceptance_criteria is True
        assert inp.has_user_flows is True
        assert len(inp.user_flows) == 1

    def test_empty_summary_raises(self):
        with pytest.raises(ValueError):
            TestGenerationInput(requirement_summary="")


class TestTestGenerationOutput:
    def test_empty_output(self):
        out = TestGenerationOutput(summary="No tests generated")
        assert out.ui_tests == []
        assert out.api_tests == []
        assert out.test_data_suggestions == []
        assert out.summary == "No tests generated"

    def test_full_output(self):
        out = TestGenerationOutput(
            summary="Generated 2 test files",
            ui_tests=[
                GeneratedTestFile(
                    filename="tests/login/login.spec.ts",
                    code='test("login", async () => {});',
                    description="Login test",
                )
            ],
            test_data_suggestions=[
                TestDataSuggestion(
                    field="email",
                    data_type="email",
                    valid_values=["user@test.com"],
                )
            ],
            prompt_tokens=100,
            completion_tokens=200,
            model_used="gpt-4o",
        )
        assert len(out.ui_tests) == 1
        assert len(out.test_data_suggestions) == 1
        assert out.ui_tests[0].filename == "tests/login/login.spec.ts"


class TestGeneratedTestFile:
    def test_defaults(self):
        f = GeneratedTestFile(filename="test.spec.ts", code="// empty")
        assert f.language == "typescript"
        assert f.framework == "playwright"
        assert f.description == ""

    def test_language_immutable(self):
        f = GeneratedTestFile(filename="test.spec.ts", code="// empty")
        assert f.language == "typescript"


class TestUserFlow:
    def test_minimal(self):
        flow = UserFlow(name="Login")
        assert flow.steps == []
        assert flow.preconditions == []
        assert flow.expected_outcomes == []

    def test_with_steps(self):
        flow = UserFlow(
            name="Login",
            steps=[UserFlowStep(action="Click login", selector="#btn")],
            preconditions=["User is on login page"],
            expected_outcomes=["User is redirected to dashboard"],
        )
        assert len(flow.steps) == 1
        assert flow.steps[0].action == "Click login"
