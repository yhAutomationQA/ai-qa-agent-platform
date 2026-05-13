import json
import structlog
from pathlib import Path
from datetime import datetime

from ai_orchestrator.models import TokenUsage
from ai_orchestrator.config import ai_config

logger = structlog.get_logger()


class TokenTracker:
    def __init__(self, log_path: str | None = None):
        self.log_path = Path(log_path or ai_config.TOKEN_LOG_PATH)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_usage: list[TokenUsage] = []

    def track(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        provider: str,
    ) -> TokenUsage:
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=model,
            provider=provider,
            timestamp=datetime.utcnow(),
        )
        usage.cost = usage.cost_usd
        self.session_usage.append(usage)
        self._log(usage)
        logger.debug(
            "token_usage",
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total=usage.total_tokens,
            cost=round(usage.cost, 6),
        )
        return usage

    def _log(self, usage: TokenUsage) -> None:
        entry = {
            "timestamp": usage.timestamp.isoformat(),
            "model": usage.model,
            "provider": usage.provider,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost": round(usage.cost, 6),
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def session_summary(self) -> dict:
        if not self.session_usage:
            return {"total_calls": 0, "total_tokens": 0, "total_cost": 0.0}

        total_calls = len(self.session_usage)
        total_tokens = sum(u.total_tokens for u in self.session_usage)
        total_cost = sum(u.cost for u in self.session_usage)

        return {
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
            "avg_tokens_per_call": round(total_tokens / total_calls, 1) if total_calls else 0,
            "by_model": self._breakdown_by_model(),
        }

    def _breakdown_by_model(self) -> dict:
        breakdown: dict[str, dict] = {}
        for u in self.session_usage:
            key = f"{u.provider}/{u.model}"
            if key not in breakdown:
                breakdown[key] = {"calls": 0, "tokens": 0, "cost": 0.0}
            breakdown[key]["calls"] += 1
            breakdown[key]["tokens"] += u.total_tokens
            breakdown[key]["cost"] += u.cost
        return breakdown

    def reset_session(self) -> None:
        self.session_usage.clear()
