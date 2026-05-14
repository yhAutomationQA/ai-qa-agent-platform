from typing import Any
from datetime import datetime, timezone

from agents.src.base.agent import BaseAgent, AgentConfig, AgentResult


class ReporterAgent(BaseAgent):
    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig(name="reporter-agent", type="reporter"))

    async def validate(self, task: dict) -> bool:
        return "results" in task

    async def execute(self, task: dict) -> AgentResult:
        results = task["results"]
        format_type = task.get("format", "json")

        report = self._generate_report(results)

        if format_type == "summary":
            report = self._generate_summary(results)

        return AgentResult(status="passed", data=report)

    async def cleanup(self) -> None:
        pass

    def _generate_report(self, results: list[dict]) -> dict:
        total = len(results)
        passed = sum(1 for r in results if r.get("status") == "passed")
        failed = sum(1 for r in results if r.get("status") == "failed")
        errors = sum(1 for r in results if r.get("status") == "error")

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "success_rate": round((passed / total * 100) if total > 0 else 0, 2),
            },
            "details": results,
        }

    def _generate_summary(self, results: list[dict]) -> str:
        report = self._generate_report(results)
        s = report["summary"]
        return (
            f"Test Report\n"
            f"{'=' * 40}\n"
            f"Total: {s['total']} | Passed: {s['passed']} | "
            f"Failed: {s['failed']} | Errors: {s['errors']}\n"
            f"Success Rate: {s['success_rate']}%\n"
            f"Generated: {report['generated_at']}"
        )
