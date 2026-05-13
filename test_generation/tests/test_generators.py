import pytest
from test_generation.src.playwright_codegen import PlaywrightCodeGenerator
from test_generation.src.api_codegen import ApiCodeGenerator
from test_generation.src.data_suggestions import DataSuggestionEngine
from test_generation.src.models import TestGenerationInput


class TestPlaywrightCodeGenerator:
    def test_generate_page_object(self):
        gen = PlaywrightCodeGenerator()
        files = gen.generate_all(
            feature_name="Login",
            page_objects=[
                {
                    "name": "Login",
                    "elements": [
                        {"name": "emailInput", "selector": "#email"},
                        {"name": "passwordInput", "selector": "#password"},
                    ],
                    "actions": [
                        {
                            "name": "login",
                            "steps": [
                                'fillField("#email", "user@test.com")',
                                'fillField("#password", "pass")',
                                'clickElement("#submit")',
                            ],
                        }
                    ],
                }
            ],
            test_cases=[
                {
                    "name": "should login with valid credentials",
                    "steps": [
                        'loginPage.login("user@test.com", "pass")',
                        'expect(page).toHaveURL("/dashboard")',
                    ],
                }
            ],
        )
        assert len(files) >= 3  # page object + fixture + spec
        assert any("LoginPage" in f.code for f in files)
        assert any("login.spec.ts" in f.filename or "login" in f.filename for f in files)

    def test_generate_from_llm_output_empty(self):
        gen = PlaywrightCodeGenerator()
        inp = TestGenerationInput(requirement_summary="Login")
        files = gen.generate_from_llm_output(inp, {})
        assert files == []

    def test_generate_from_llm_output_with_code(self):
        gen = PlaywrightCodeGenerator()
        inp = TestGenerationInput(requirement_summary="Login Feature")
        llm_out = {"code": "```typescript\ntest('login', async () => {});\n```"}
        files = gen.generate_from_llm_output(inp, llm_out)
        assert len(files) == 1
        assert ".spec.ts" in files[0].filename


class TestApiCodeGenerator:
    def test_generate_all(self):
        gen = ApiCodeGenerator()
        scenarios = [
            {
                "endpoint": "POST /api/login",
                "method": "POST",
                "path": "/api/login",
                "tests": [
                    {
                        "name": "should login successfully",
                        "type": "positive",
                        "expected_status": 200,
                        "auth_required": False,
                        "request": {"body": {"email": "user@test.com", "password": "pass"}},
                        "assertions": ["status is 200", "body has token field"],
                    }
                ],
            }
        ]
        files = gen.generate_all(scenarios)
        assert len(files) == 1
        assert "api-tests.spec.ts" in files[0].filename

    def test_generate_from_llm_output_with_list(self):
        gen = ApiCodeGenerator()
        inp = TestGenerationInput(requirement_summary="Login API")
        llm_out = {
            "scenarios": [
                {
                    "endpoint": "GET /api/health",
                    "method": "GET",
                    "path": "/api/health",
                    "tests": [{"name": "health check", "type": "positive", "expected_status": 200}],
                }
            ]
        }
        files = gen.generate_from_llm_output(inp, llm_out)
        assert len(files) == 1


class TestDataSuggestionEngine:
    def test_suggest_for_input_with_email(self):
        engine = DataSuggestionEngine()
        inp = TestGenerationInput(
            requirement_summary="User registration with email and password"
        )
        suggestions = engine.suggest_for_input(inp)
        assert len(suggestions) >= 1
        types = {s.data_type for s in suggestions}
        assert "email" in types or "password" in types

    def test_suggest_for_input_without_keywords(self):
        engine = DataSuggestionEngine()
        inp = TestGenerationInput(requirement_summary="Xyzzy feature")
        suggestions = engine.suggest_for_input(inp)
        assert len(suggestions) >= 1

    def test_parse_llm_suggestions_valid(self):
        engine = DataSuggestionEngine()
        inp = TestGenerationInput(requirement_summary="Login")
        llm_out = {
            "suggestions": [
                {
                    "field": "username",
                    "data_type": "text",
                    "valid_values": ["admin", "user"],
                    "invalid_values": [""],
                    "edge_values": ["a" * 100],
                    "description": "Username field",
                }
            ]
        }
        suggestions = engine.parse_llm_suggestions(inp, llm_out)
        assert len(suggestions) == 1
        assert suggestions[0].field == "username"

    def test_parse_llm_suggestions_empty_falls_back(self):
        engine = DataSuggestionEngine()
        inp = TestGenerationInput(requirement_summary="Login")
        suggestions = engine.parse_llm_suggestions(inp, {})
        assert len(suggestions) >= 1
