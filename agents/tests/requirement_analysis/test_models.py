import pytest
from datetime import datetime

from agents.src.requirement_analysis.models import (
    RequirementAnalysisInput,
    RequirementAnalysisOutput,
    RequirementSummary,
    FunctionalScenario,
    EdgeCase,
    NegativeScenario,
    RiskArea,
    MissingRequirement,
    AnalysisMetadata,
)


class TestRequirementAnalysisInput:
    def test_minimal_input(self):
        inp = RequirementAnalysisInput(summary="Test story")
        assert inp.summary == "Test story"
        assert inp.acceptance_criteria == []
        assert inp.comments == []

    def test_full_input(self):
        inp = RequirementAnalysisInput(
            issue_key="PROJ-123",
            summary="User login",
            description="As a user, I want to log in",
            acceptance_criteria=["AC1: Valid login works", "AC2: Invalid shows error"],
            comments=[{"author": {"displayName": "Bob"}, "body": "Needs SSO"}],
            labels=["auth", "frontend"],
            priority="high",
        )
        assert inp.issue_key == "PROJ-123"
        assert len(inp.acceptance_criteria) == 2


class TestRequirementSummary:
    def test_defaults(self):
        s = RequirementSummary()
        assert s.complexity == "medium"
        assert s.key_functionality == []


class TestFunctionalScenario:
    def test_default_id_format(self):
        s = FunctionalScenario(title="Test login")
        assert s.title == "Test login"
        assert s.priority == "medium"


class TestEdgeCase:
    def test_default_category(self):
        e = EdgeCase(title="Empty input")
        assert e.category == "boundary"
        assert e.severity == "medium"


class TestNegativeScenario:
    def test_default_attack_vector(self):
        n = NegativeScenario(title="SQL injection")
        assert n.attack_vector == "input_validation"


class TestRiskArea:
    def test_defaults(self):
        r = RiskArea(area="Performance")
        assert r.likelihood == "medium"
        assert r.impact == "medium"


class TestMissingRequirement:
    def test_defaults(self):
        m = MissingRequirement(title="Error handling")
        assert m.priority == "medium"


class TestAnalysisMetadata:
    def test_auto_timestamp(self):
        m = AnalysisMetadata()
        assert isinstance(m.analyzed_at, datetime)

    def test_custom_values(self):
        m = AnalysisMetadata(model_used="gpt-4o", total_tokens=500, processing_time_ms=1234.5, source_issue_key="PROJ-1")
        assert m.model_used == "gpt-4o"
        assert m.total_tokens == 500


class TestRequirementAnalysisOutput:
    def test_empty_output_defaults(self):
        out = RequirementAnalysisOutput()
        assert out.functional_scenarios == []
        assert out.edge_cases == []
        assert out.negative_scenarios == []
        assert out.risk_areas == []
        assert out.missing_requirements == []
        assert out.summary.complexity == "medium"

    def test_output_with_data(self):
        out = RequirementAnalysisOutput(
            summary=RequirementSummary(overall_purpose="Login feature", complexity="low"),
            functional_scenarios=[FunctionalScenario(title="Happy path")],
            edge_cases=[EdgeCase(title="Null password")],
            negative_scenarios=[NegativeScenario(title="Brute force")],
            risk_areas=[RiskArea(area="Security")],
            missing_requirements=[MissingRequirement(title="2FA")],
        )
        assert out.summary.overall_purpose == "Login feature"
        assert len(out.functional_scenarios) == 1
        assert len(out.edge_cases) == 1
        assert len(out.negative_scenarios) == 1
        assert len(out.risk_areas) == 1
        assert len(out.missing_requirements) == 1
