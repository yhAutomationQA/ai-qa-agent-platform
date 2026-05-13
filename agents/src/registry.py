from typing import Any
import structlog

from agents.src.base.agent import BaseAgent
from agents.src.browser.agent import BrowserAgent
from agents.src.api.agent import APIAgent
from agents.src.planner.agent import PlannerAgent
from agents.src.reporter.agent import ReporterAgent

logger = structlog.get_logger()

_registry: dict[str, type[BaseAgent]] = {}


def register_agent(name: str, agent_class: type[BaseAgent]) -> None:
    _registry[name] = agent_class
    logger.info("agent_registered", name=name, class_name=agent_class.__name__)


def get_agent(name: str, **kwargs: Any) -> BaseAgent:
    agent_class = _registry.get(name)
    if not agent_class:
        raise KeyError(f"Agent not found in registry: {name}")
    return agent_class(**kwargs)


def list_agents() -> dict[str, type[BaseAgent]]:
    return dict(_registry)


register_agent("browser", BrowserAgent)
register_agent("api", APIAgent)
register_agent("planner", PlannerAgent)
register_agent("reporter", ReporterAgent)
