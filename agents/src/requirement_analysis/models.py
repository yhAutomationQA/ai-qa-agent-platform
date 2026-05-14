from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums for constrained fields ──────────────────────────

class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AttackVector(str, Enum):
    INJECTION = "injection"
    AUTH_BYPASS = "auth_bypass"
    INPUT_VALIDATION = "input_validation"
    BUSINESS_LOGIC = "business_logic"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    PROTOCOL_VIOLATION = "protocol_violation"


class EdgeCategory(str, Enum):
    BOUNDARY = "boundary"
    EMPTY_NULL = "empty/null"
    FORMAT = "format"
    CONCURRENCY = "concurrency"
    STATE = "state"
    DATA_TYPE = "data_type"


class Likelihood(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Impact(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ── Input ─────────────────────────────────────────────────

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


# ── Response sections ─────────────────────────────────────

class RequirementSummary(BaseModel):
    overall_purpose: str = ""
    key_functionality: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    complexity: Complexity = Complexity.MEDIUM


class FunctionalScenario(BaseModel):
    id: str = ""
    title: str = ""
    description: str = ""
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    expected_result: str = ""
    relates_to_ac: str = ""
    priority: Priority = Priority.MEDIUM


class EdgeCase(BaseModel):
    id: str = ""
    title: str = ""
    description: str = ""
    input_condition: str = ""
    expected_behavior: str = ""
    severity: Severity = Severity.MEDIUM
    category: EdgeCategory = EdgeCategory.BOUNDARY


class NegativeScenario(BaseModel):
    id: str = ""
    title: str = ""
    description: str = ""
    malicious_input: str = ""
    expected_failure: str = ""
    attack_vector: AttackVector = AttackVector.INPUT_VALIDATION
    severity: Severity = Severity.MEDIUM


class RiskArea(BaseModel):
    area: str = ""
    description: str = ""
    likelihood: Likelihood = Likelihood.MEDIUM
    impact: Impact = Impact.MEDIUM
    mitigation: str = ""


class MissingRequirement(BaseModel):
    title: str = ""
    description: str = ""
    rationale: str = ""
    suggested_action: str = ""
    priority: Priority = Priority.MEDIUM


# ── Per-section validator wrappers ────────────────────────

class SectionValidation(BaseModel):
    valid_count: int = 0
    failed_count: int = 0
    errors: list[str] = Field(default_factory=list)


class ParsedSections(BaseModel):
    summary: RequirementSummary = Field(default_factory=RequirementSummary)
    functional_scenarios: list[FunctionalScenario] = Field(default_factory=list)
    edge_cases: list[EdgeCase] = Field(default_factory=list)
    negative_scenarios: list[NegativeScenario] = Field(default_factory=list)
    risk_areas: list[RiskArea] = Field(default_factory=list)
    missing_requirements: list[MissingRequirement] = Field(default_factory=list)
    validation: dict[str, SectionValidation] = Field(default_factory=dict)


# ── Raw AI response (before validation) ───────────────────

class RawAIResponse(BaseModel):
    raw_text: str = ""
    extracted_json: str = ""
    parse_error: str | None = None
    parsed_data: dict[str, Any] = Field(default_factory=dict)


# ── Metadata ──────────────────────────────────────────────

class AnalysisMetadata(BaseModel):
    model_used: str = ""
    total_tokens: int = 0
    processing_time_ms: float = 0.0
    source_issue_key: str = ""
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Final output ──────────────────────────────────────────

class RequirementAnalysisOutput(BaseModel):
    summary: RequirementSummary = Field(default_factory=RequirementSummary)
    functional_scenarios: list[FunctionalScenario] = Field(default_factory=list)
    edge_cases: list[EdgeCase] = Field(default_factory=list)
    negative_scenarios: list[NegativeScenario] = Field(default_factory=list)
    risk_areas: list[RiskArea] = Field(default_factory=list)
    missing_requirements: list[MissingRequirement] = Field(default_factory=list)
    metadata: AnalysisMetadata = Field(default_factory=AnalysisMetadata)
