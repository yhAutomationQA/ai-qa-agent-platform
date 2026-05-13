import structlog
from typing import Any

from ai_orchestrator.src.llm.client import LLMClient
from ai_orchestrator.src.memory.store import MemoryStore

logger = structlog.get_logger()


class OrchestratorAgent:
    def __init__(self, llm: LLMClient, memory: MemoryStore):
        self.llm = llm
        self.memory = memory
        self.sub_agents: dict[str, Any] = {}

    def register_agent(self, name: str, agent: Any) -> None:
        self.sub_agents[name] = agent
        logger.info("agent_registered", name=name)

    async def delegate(self, task: dict) -> dict:
        agent_type = task.get("agent_type", "browser")
        agent = self.sub_agents.get(agent_type)
        if not agent:
            raise ValueError(f"No agent registered for type: {agent_type}")

        logger.info("delegating_task", agent_type=agent_type, task=task.get("name"))
        return await agent.execute(task)

    async def plan(self, objective: str) -> list[dict]:
        prompt = f"Create a step-by-step test plan for: {objective}"
        plan_text = await self.llm.generate(prompt)
        return [{"step": i, "description": step.strip()} for i, step in enumerate(plan_text.split("\n"), 1) if step.strip()]
