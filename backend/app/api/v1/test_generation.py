from typing import Annotated

from fastapi import APIRouter, Body

from test_generation.src.models import (
    TestGenerationInput,
    TestGenerationOutput,
)
from test_generation.src.generator import TestGenerator

router = APIRouter()


@router.post("/generate", response_model=TestGenerationOutput)
async def generate_tests(
    input_data: TestGenerationInput = Body(
        ...,
        examples=[
            {
                "requirement_summary": "User login with email and password",
                "acceptance_criteria": [
                    "Email field accepts valid email format",
                    "Password field hides input",
                    "Show error on invalid credentials",
                    "Redirect to dashboard on success",
                ],
                "user_flows": [
                    {
                        "name": "Successful login",
                        "description": "User logs in with valid credentials",
                        "steps": [
                            {"action": "Enter email", "selector": "#email"},
                            {"action": "Enter password", "selector": "#password"},
                            {"action": "Click login button", "selector": "#login-btn"},
                        ],
                        "expected_outcomes": ["User redirected to dashboard"],
                    }
                ],
                "technology_stack": "nextjs",
                "test_types": ["ui", "api"],
            }
        ],
    ),
):
    generator = TestGenerator()
    output = await generator.generate(input_data)
    return output


@router.post("/generate/ui", response_model=TestGenerationOutput)
async def generate_ui_tests(
    input_data: TestGenerationInput = Body(...),
):
    input_data.test_types = ["ui"]
    generator = TestGenerator()
    output = await generator.generate(input_data)
    return output


@router.post("/generate/api", response_model=TestGenerationOutput)
async def generate_api_tests(
    input_data: TestGenerationInput = Body(...),
):
    input_data.test_types = ["api"]
    generator = TestGenerator()
    output = await generator.generate(input_data)
    return output


@router.post("/generate/data", response_model=TestGenerationOutput)
async def generate_test_data(
    input_data: TestGenerationInput = Body(...),
):
    generator = TestGenerator()
    input_data.test_types = []
    output = await generator._generate_test_data(
        input_data,
        f"## Requirement Summary\n{input_data.requirement_summary}",
    )
    from test_generation.src.models import TestGenerationOutput, GeneratedTestFile

    return TestGenerationOutput(
        summary=f"Generated {len(output['suggestions'])} test data suggestions",
        test_data_suggestions=output["suggestions"],
        prompt_tokens=output["prompt_tokens"],
        completion_tokens=output["completion_tokens"],
        model_used="gpt-4o",
    )
