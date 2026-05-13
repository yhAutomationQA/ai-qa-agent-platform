from typing import Any

from agents.src.base.agent import BaseAgent, AgentConfig, AgentResult
from agents.src.requirement_analysis.models import RequirementAnalysisInput
from agents.src.requirement_analysis.analyzer import RequirementAnalyzer


class RequirementAnalysisAgent(BaseAgent):
    def __init__(self, config: AgentConfig | None = None, llm_client: Any = None):
        super().__init__(
            config or AgentConfig(name="requirement-analysis-agent", type="requirement_analysis")
        )
        self._llm = llm_client
        self._analyzer: RequirementAnalyzer | None = None

    @property
    def analyzer(self) -> RequirementAnalyzer:
        if self._analyzer is None:
            if self._llm is None:
                from ai_orchestrator.src.llm.client import LLMClient
                self._llm = LLMClient()
            self._analyzer = RequirementAnalyzer(llm_client=self._llm)
        return self._analyzer

    async def validate(self, task: dict) -> bool:
        return bool(task.get("summary") or task.get("description") or task.get("issue_key"))

    async def execute(self, task: dict) -> AgentResult:
        input_data = RequirementAnalysisInput(
            issue_key=task.get("issue_key", ""),
            summary=task.get("summary", ""),
            description=task.get("description", ""),
            acceptance_criteria=task.get("acceptance_criteria", []),
            comments=task.get("comments", []),
            labels=task.get("labels", []),
            priority=task.get("priority", ""),
            issue_type=task.get("issue_type", "story"),
            project_key=task.get("project_key", ""),
        )

        output = await self.analyzer.analyze(input_data)

        return AgentResult(
            status="passed",
            data=output.model_dump(),
            artifacts=[
                f"scenarios:{len(output.functional_scenarios)}",
                f"edge_cases:{len(output.edge_cases)}",
                f"negative:{len(output.negative_scenarios)}",
                f"risks:{len(output.risk_areas)}",
                f"gaps:{len(output.missing_requirements)}",
            ],
        )

    async def cleanup(self) -> None:
        pass
