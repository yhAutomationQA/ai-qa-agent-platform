from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RequirementAnalysisInput(BaseModel):
    issue_key: str = ""
    summary: str = ""
    description: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    comments: list[dict[str, Any]] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    priority: str = ""
    issue_type: str = "story"
    project_key: str = ""


class RequirementSummary(BaseModel):
    overall_purpose: str = ""
    key_functionality: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    complexity: str = "medium"


class FunctionalScenario(BaseModel):
    id: str = ""
    title: str = ""
    description: str = ""
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    expected_result: str = ""
    relates_to_ac: str = ""
    priority: str = "medium"


class EdgeCase(BaseModel):
    id: str = ""
    title: str = ""
    description: str = ""
    input_condition: str = ""
    expected_behavior: str = ""
    severity: str = "medium"
    category: str = "boundary"


class NegativeScenario(BaseModel):
    id: str = ""
    title: str = ""
    description: str = ""
    malicious_input: str = ""
    expected_failure: str = ""
    attack_vector: str = "input_validation"
    severity: str = "medium"


class RiskArea(BaseModel):
    area: str = ""
    description: str = ""
    likelihood: str = "medium"
    impact: str = "medium"
    mitigation: str = ""


class MissingRequirement(BaseModel):
    title: str = ""
    description: str = ""
    rationale: str = ""
    suggested_action: str = ""
    priority: str = "medium"


class AnalysisMetadata(BaseModel):
    model_used: str = ""
    total_tokens: int = 0
    processing_time_ms: float = 0.0
    source_issue_key: str = ""
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class RequirementAnalysisOutput(BaseModel):
    summary: RequirementSummary = Field(default_factory=RequirementSummary)
    functional_scenarios: list[FunctionalScenario] = Field(default_factory=list)
    edge_cases: list[EdgeCase] = Field(default_factory=list)
    negative_scenarios: list[NegativeScenario] = Field(default_factory=list)
    risk_areas: list[RiskArea] = Field(default_factory=list)
    missing_requirements: list[MissingRequirement] = Field(default_factory=list)
    metadata: AnalysisMetadata = Field(default_factory=AnalysisMetadata)
