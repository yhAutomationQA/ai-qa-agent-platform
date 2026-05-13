from typing import Any

import httpx

from agents.src.base.agent import BaseAgent, AgentConfig, AgentResult


class APIAgent(BaseAgent):
    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig(name="api-agent", type="api"))

    async def validate(self, task: dict) -> bool:
        return "method" in task and "url" in task

    async def execute(self, task: dict) -> AgentResult:
        method = task["method"].upper()
        url = task["url"]
        headers = task.get("headers", {})
        params = task.get("params", {})
        body = task.get("body")
        expected_status = task.get("expected_status")

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=body,
            )

            status_match = (
                response.status_code == expected_status if expected_status else True
            )

            return AgentResult(
                status="passed" if status_match else "failed",
                data={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    "duration_ms": response.elapsed.total_seconds() * 1000,
                },
            )

    async def cleanup(self) -> None:
        pass
