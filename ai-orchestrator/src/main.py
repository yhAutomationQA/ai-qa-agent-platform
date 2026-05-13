import structlog

from ai_orchestrator.src.pipeline.pipeline import TestPipeline
from ai_orchestrator.src.llm.client import LLMClient
from ai_orchestrator.src.memory.store import MemoryStore
from ai_orchestrator.src.config import OrchestratorConfig

logger = structlog.get_logger()


class AIOrchestrator:
    def __init__(self, config: OrchestratorConfig | None = None):
        self.config = config or OrchestratorConfig()
        self.llm = LLMClient(config=self.config)
        self.memory = MemoryStore(redis_url=self.config.REDIS_URL)
        self.pipeline = TestPipeline(llm=self.llm, memory=self.memory)

    async def execute_test_run(self, test_spec: dict) -> dict:
        logger.info("starting_test_run", test_name=test_spec.get("name"))
        result = await self.pipeline.run(test_spec)
        logger.info("test_run_completed", status=result.get("status"))
        return result

    async def generate_test_case(self, requirements: str) -> dict:
        logger.info("generating_test_case")
        prompt = f"Generate a comprehensive test case for: {requirements}"
        response = await self.llm.generate(prompt)
        return {"requirements": requirements, "test_case": response}

    async def analyze_results(self, run_results: dict) -> dict:
        logger.info("analyzing_results")
        analysis = await self.llm.generate(
            f"Analyze these test results and provide insights: {run_results}"
        )
        return {"analysis": analysis}


orchestrator = AIOrchestrator()
