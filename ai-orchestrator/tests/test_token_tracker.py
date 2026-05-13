import pytest
import json
import tempfile
from pathlib import Path

from ai_orchestrator.core.token_tracker import TokenTracker
from ai_orchestrator.models import TokenUsage


@pytest.fixture
def tracker():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield TokenTracker(log_path=str(Path(tmpdir) / "tokens.jsonl"))


class TestTokenTracker:
    def test_track_adds_usage(self, tracker: TokenTracker):
        usage = tracker.track(
            prompt_tokens=100,
            completion_tokens=50,
            model="gpt-4o",
            provider="openai",
        )
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.model == "gpt-4o"
        assert usage.provider == "openai"

    def test_track_writes_to_log(self, tracker: TokenTracker):
        tracker.track(prompt_tokens=10, completion_tokens=5, model="gpt-4o", provider="openai")
        lines = tracker.log_path.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["total_tokens"] == 15
        assert entry["model"] == "gpt-4o"

    def test_session_summary_empty(self, tracker: TokenTracker):
        summary = tracker.session_summary()
        assert summary["total_calls"] == 0
        assert summary["total_tokens"] == 0

    def test_session_summary_with_calls(self, tracker: TokenTracker):
        tracker.track(prompt_tokens=100, completion_tokens=50, model="gpt-4o", provider="openai")
        tracker.track(prompt_tokens=200, completion_tokens=100, model="gpt-4o", provider="openai")

        summary = tracker.session_summary()
        assert summary["total_calls"] == 2
        assert summary["total_tokens"] == 450
        assert summary["avg_tokens_per_call"] == 225.0

    def test_session_summary_breakdown_by_model(self, tracker: TokenTracker):
        tracker.track(prompt_tokens=100, completion_tokens=50, model="gpt-4o", provider="openai")
        summary = tracker.session_summary()
        assert "openai/gpt-4o" in summary["by_model"]
        assert summary["by_model"]["openai/gpt-4o"]["calls"] == 1

    def test_reset_session(self, tracker: TokenTracker):
        tracker.track(prompt_tokens=50, completion_tokens=25, model="gpt-4o", provider="openai")
        assert tracker.session_summary()["total_calls"] == 1
        tracker.reset_session()
        assert tracker.session_summary()["total_calls"] == 0

    def test_cost_calculation_gpt4o(self):
        usage = TokenUsage(
            prompt_tokens=1000,
            completion_tokens=500,
            model="gpt-4o",
            provider="openai",
        )
        expected_cost = (1.0 * 2.50) + (0.5 * 10.00)
        assert usage.cost_usd == expected_cost
