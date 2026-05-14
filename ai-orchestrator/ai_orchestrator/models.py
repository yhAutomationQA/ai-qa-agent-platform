from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timezone


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    provider: str = ""
    cost: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def cost_usd(self) -> float:
        rates = {
            "gpt-4o": (2.50, 10.00),
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4-turbo": (10.00, 30.00),
            "claude-sonnet-4-20250514": (3.00, 15.00),
            "claude-3-haiku": (0.25, 1.25),
        }
        per_1k_input, per_1k_output = rates.get(self.model, (0, 0))
        return (self.prompt_tokens / 1000 * per_1k_input) + (
            self.completion_tokens / 1000 * per_1k_output
        )


@dataclass
class LLMResponse:
    content: str
    token_usage: TokenUsage | None = None
    finish_reason: str = ""
    raw_response: Any = None


@dataclass
class TestScenario:
    id: str = ""
    title: str = ""
    description: str = ""
    preconditions: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    expected_results: list[str] = field(default_factory=list)
    test_data: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    priority: str = "medium"
    category: str = "functional"
    generated_from: str = ""


@dataclass
class RequirementSummary:
    original_length: int = 0
    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    stakeholders: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    risk_areas: list[str] = field(default_factory=list)
    estimated_effort: str = ""


@dataclass
class EdgeCase:
    title: str = ""
    description: str = ""
    input_condition: str = ""
    expected_behavior: str = ""
    severity: str = "medium"
    category: str = "boundary"


@dataclass
class NegativeScenario:
    title: str = ""
    description: str = ""
    malicious_input: str = ""
    expected_failure: str = ""
    attack_vector: str = ""
    severity: str = "medium"
