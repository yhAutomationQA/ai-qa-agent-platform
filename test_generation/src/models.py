from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field
from typing import Literal


class UserFlowStep(BaseModel):
    action: str
    selector: str | None = None
    value: str | None = None
    wait_after: int | None = None


class UserFlow(BaseModel):
    name: str
    description: str = ""
    steps: list[UserFlowStep] = []
    preconditions: list[str] = []
    expected_outcomes: list[str] = []


class TestType(str, Enum):
    UI = "ui"
    API = "api"
    BOTH = "both"


class Framework(str, Enum):
    REACT = "react"
    ANGULAR = "angular"
    VUE = "vue"
    NEXTJS = "nextjs"
    UNKNOWN = "unknown"


class TestGenerationInput(BaseModel):
    requirement_summary: str = Field(..., min_length=1, description="Brief summary of the feature")
    acceptance_criteria: list[str] = Field(default_factory=list, description="List of acceptance criteria")
    user_flows: list[UserFlow] = Field(default_factory=list, description="User flow descriptions")
    technology_stack: Framework = Field(default=Framework.NEXTJS, description="Frontend framework")
    test_types: list[TestType] = Field(default=[TestType.UI, TestType.API], description="Types of tests to generate")
    additional_context: str = Field("", description="Any extra context about the feature")

    @property
    def has_acceptance_criteria(self) -> bool:
        return len(self.acceptance_criteria) > 0

    @property
    def has_user_flows(self) -> bool:
        return len(self.user_flows) > 0


class GeneratedTestFile(BaseModel):
    filename: str = Field(..., description="Suggested filename with extension")
    language: Literal["typescript"] = "typescript"
    framework: Literal["playwright"] = "playwright"
    code: str = Field(..., description="Complete test file source code")
    description: str = Field("", description="Human-readable description of this test")


class TestDataSuggestion(BaseModel):
    field: str = Field(..., description="Form field or parameter name")
    data_type: str = Field(..., description="Type of test data")
    valid_values: list[str] = Field(default_factory=list, description="Valid test values")
    invalid_values: list[str] = Field(default_factory=list, description="Invalid/boundary values")
    edge_values: list[str] = Field(default_factory=list, description="Edge case values")
    description: str = Field("", description="Explanation of the test data strategy")


class TestGenerationOutput(BaseModel):
    ui_tests: list[GeneratedTestFile] = Field(default_factory=list)
    api_tests: list[GeneratedTestFile] = Field(default_factory=list)
    test_data_suggestions: list[TestDataSuggestion] = Field(default_factory=list)
    summary: str = Field(..., description="Summary of what was generated")
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model_used: str = ""
