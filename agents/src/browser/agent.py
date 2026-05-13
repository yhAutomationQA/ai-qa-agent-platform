from typing import Any

from playwright.async_api import async_playwright, Browser, Page

from agents.src.base.agent import BaseAgent, AgentConfig, AgentResult


class BrowserAgent(BaseAgent):
    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig(name="browser-agent", type="browser"))
        self._browser: Browser | None = None
        self._page: Page | None = None

    async def validate(self, task: dict) -> bool:
        return "url" in task or "action" in task

    async def execute(self, task: dict) -> AgentResult:
        url = task.get("url")
        action = task.get("action", "navigate")
        selector = task.get("selector")
        value = task.get("value")

        async with async_playwright() as p:
            browser_type = getattr(p, self.config.parameters.get("browser", "chromium"))
            self._browser = await browser_type.launch(headless=self.config.headless)
            context = await self._browser.new_context(
                viewport={"width": 1280, "height": 720}
            )
            self._page = await context.new_page()

            if action == "navigate" and url:
                await self._page.goto(url, timeout=self.config.timeout * 1000)
                return AgentResult(
                    status="passed",
                    data={"url": url, "title": await self._page.title()},
                )

            elif action == "click" and selector:
                await self._page.click(selector)
                return AgentResult(status="passed", data={"action": "click", "selector": selector})

            elif action == "type" and selector and value:
                await self._page.fill(selector, value)
                return AgentResult(
                    status="passed", data={"action": "type", "selector": selector}
                )

            elif action == "screenshot":
                screenshot = await self._page.screenshot(full_page=True)
                return AgentResult(
                    status="passed",
                    data={"screenshot_size": len(screenshot)},
                    artifacts=["screenshot"],
                )

            elif action == "extract" and selector:
                element = await self._page.query_selector(selector)
                text = await element.inner_text() if element else ""
                return AgentResult(
                    status="passed",
                    data={"selector": selector, "text": text},
                )

            return AgentResult(status="failed", error=f"Unsupported action: {action}")

    async def cleanup(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None
