from typing import Any

from agents.src.base.agent import BaseAgent, AgentConfig, AgentResult


class PlannerAgent(BaseAgent):
    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig(name="planner-agent", type="planner"))

    async def validate(self, task: dict) -> bool:
        return "objective" in task

    async def execute(self, task: dict) -> AgentResult:
        objective = task["objective"]
        constraints = task.get("constraints", [])

        plan = {
            "objective": objective,
            "steps": [
                {"order": i + 1, "action": step}
                for i, step in enumerate(self._decompose(objective))
            ],
            "constraints": constraints,
            "estimated_duration": len(objective.split()) * 5,
        }

        return AgentResult(status="passed", data=plan)

    async def cleanup(self) -> None:
        pass

    def _decompose(self, objective: str) -> list[str]:
        return [
            f"Analyze: {objective}",
            "Prepare test environment",
            "Execute test scenario",
            "Verify expected behavior",
            "Clean up resources",
            "Generate test report",
        ]
