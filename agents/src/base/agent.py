from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class AgentConfig:
    name: str = ""
    type: str = "base"
    timeout: int = 300
    max_retries: int = 3
    headless: bool = True
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    status: str = "pending"
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0
    artifacts: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class BaseAgent(ABC):
    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self.logger = logger.bind(agent=self.config.name, type=self.config.type)

    @abstractmethod
    async def execute(self, task: dict) -> AgentResult:
        ...

    @abstractmethod
    async def validate(self, task: dict) -> bool:
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        ...

    async def run(self, task: dict) -> AgentResult:
        self.logger.info("agent_execution_started", task=task.get("name"))
        started = datetime.utcnow()

        if not await self.validate(task):
            return AgentResult(status="invalid", error="Task validation failed")

        try:
            result = await self.execute(task)
            result.started_at = started
            result.completed_at = datetime.utcnow()
            result.duration_ms = (
                result.completed_at - result.started_at
            ).total_seconds() * 1000
            self.logger.info("agent_execution_completed", status=result.status)
            return result
        except Exception as e:
            self.logger.error("agent_execution_failed", error=str(e))
            return AgentResult(
                status="error",
                error=str(e),
                started_at=started,
                completed_at=datetime.utcnow(),
            )
        finally:
            await self.cleanup()
