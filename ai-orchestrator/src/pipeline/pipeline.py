import structlog
from typing import Any
from datetime import datetime

from ai_orchestrator.src.llm.client import LLMClient
from ai_orchestrator.src.memory.store import MemoryStore
from ai_orchestrator.src.agents.orchestrator_agent import OrchestratorAgent

logger = structlog.get_logger()


class PipelineStage:
    PLAN = "plan"
    EXECUTE = "execute"
    ANALYZE = "analyze"
    REPORT = "report"


class TestPipeline:
    def __init__(self, llm: LLMClient, memory: MemoryStore):
        self.llm = llm
        self.memory = memory
        self.orchestrator = OrchestratorAgent(llm=llm, memory=memory)

    async def run(self, test_spec: dict) -> dict:
        pipeline_id = test_spec.get("id", datetime.utcnow().isoformat())
        logger.info("pipeline_started", pipeline_id=pipeline_id)

        stages = {
            PipelineStage.PLAN: self._plan_stage,
            PipelineStage.EXECUTE: self._execute_stage,
            PipelineStage.ANALYZE: self._analyze_stage,
            PipelineStage.REPORT: self._report_stage,
        }

        context: dict[str, Any] = {"spec": test_spec, "results": [], "artifacts": {}}

        for stage_name, stage_fn in stages.items():
            logger.info("pipeline_stage", stage=stage_name)
            context = await stage_fn(context)
            await self.memory.store(pipeline_id, stage_name, context)

        logger.info("pipeline_completed", pipeline_id=pipeline_id)
        return context

    async def _plan_stage(self, context: dict) -> dict:
        plan = await self.orchestrator.plan(context["spec"].get("objective", ""))
        return {**context, "plan": plan}

    async def _execute_stage(self, context: dict) -> dict:
        plan = context.get("plan", [])
        results = []
        for step in plan:
            task = {"name": step["description"], "agent_type": "browser"}
            result = await self.orchestrator.delegate(task)
            results.append(result)
        return {**context, "results": results}

    async def _analyze_stage(self, context: dict) -> dict:
        prompt = f"Analyze these test execution results: {context.get('results', [])}"
        analysis = await self.llm.generate(prompt)
        return {**context, "analysis": analysis}

    async def _report_stage(self, context: dict) -> dict:
        report = {
            "status": "completed",
            "summary": f"Executed {len(context.get('results', []))} test steps",
            "passed": sum(1 for r in context.get("results", []) if r.get("status") == "passed"),
            "failed": sum(1 for r in context.get("results", []) if r.get("status") == "failed"),
            "analysis": context.get("analysis"),
        }
        return {**context, "report": report}
