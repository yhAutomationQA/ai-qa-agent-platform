from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
from enum import Enum


class FailureCategory(str, Enum):
    ASSERTION = "assertion"
    TIMEOUT = "timeout"
    INFRASTRUCTURE = "infrastructure"
    ENVIRONMENT = "environment"
    DATA = "data"
    FLAKY = "flaky"
    DEPENDENCY = "dependency"
    STATE = "state"
    PERMISSION = "permission"
    NETWORK = "network"
    UI = "ui"
    API = "api"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisInput(BaseModel):
    test_name: str = ""
    test_suite: str = ""
    status: str = "failed"
    error_message: str | None = None
    stack_trace: str | None = None
    logs: list[str] = Field(default_factory=list)
    api_response: str | None = None
    api_status_code: int | None = None
    api_request_url: str | None = None
    api_request_body: str | None = None
    screenshot_path: str | None = None
    execution_id: str | None = None
    execution_type: str = "playwright"
    duration_ms: float | None = None
    retry_count: int = 0
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchAnalysisInput(BaseModel):
    failures: list[AnalysisInput] = Field(default_factory=list)
    run_id: str | None = None
    total_tests: int = 0
    total_passed: int = 0
    total_failed: int = 0
    total_skipped: int = 0


class RootCauseSuggestion(BaseModel):
    title: str = ""
    description: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    suggested_fix: str | None = None


class FailureCategoryResult(BaseModel):
    primary_category: FailureCategory = FailureCategory.UNKNOWN
    secondary_categories: list[FailureCategory] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = ""


class RiskAssessment(BaseModel):
    level: RiskLevel = RiskLevel.LOW
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    impacted_areas: list[str] = Field(default_factory=list)
    blast_radius: str = ""
    reasoning: str = ""


class RetryRecommendation(BaseModel):
    should_retry: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = ""
    suggested_max_retries: int = Field(default=1, ge=0, le=10)
    suggested_delay_seconds: float = Field(default=2.0, ge=0.0, le=300.0)
    conditions: list[str] = Field(default_factory=list)


class AnalysisSummary(BaseModel):
    one_liner: str = ""
    detailed_summary: str = ""
    key_findings: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    severity: RiskLevel = RiskLevel.LOW


class FailureAnalysis(BaseModel):
    analysis_id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex[:12])
    input: AnalysisInput = Field(default_factory=AnalysisInput)
    root_cause: RootCauseSuggestion = Field(default_factory=RootCauseSuggestion)
    category: FailureCategoryResult = Field(default_factory=FailureCategoryResult)
    risk: RiskAssessment = Field(default_factory=RiskAssessment)
    retry: RetryRecommendation = Field(default_factory=RetryRecommendation)
    summary: AnalysisSummary = Field(default_factory=AnalysisSummary)
    ai_used: bool = False
    ai_fallback: bool = False
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: float | None = None


class BatchAnalysisResult(BaseModel):
    analyses: list[FailureAnalysis] = Field(default_factory=list)
    category_distribution: dict[str, int] = Field(default_factory=dict)
    risk_distribution: dict[str, int] = Field(default_factory=dict)
    overall_risk: RiskLevel = RiskLevel.LOW
    top_issues: list[str] = Field(default_factory=list)
    retry_summary: dict[str, Any] = Field(default_factory=dict)
    total_analyzed: int = 0
    analysis_duration_ms: float = 0.0
