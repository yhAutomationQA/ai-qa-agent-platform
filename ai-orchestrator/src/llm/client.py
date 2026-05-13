from typing import Any
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from ai_orchestrator.src.config import OrchestratorConfig

logger = structlog.get_logger()


class LLMClient:
    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self._openai: AsyncOpenAI | None = None
        self._anthropic: AsyncAnthropic | None = None

    @property
    def openai(self) -> AsyncOpenAI:
        if self._openai is None:
            self._openai = AsyncOpenAI(api_key=self.config.OPENAI_API_KEY)
        return self._openai

    @property
    def anthropic(self) -> AsyncAnthropic:
        if self._anthropic is None:
            self._anthropic = AsyncAnthropic(api_key=self.config.ANTHROPIC_API_KEY)
        return self._anthropic

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        provider = self.config.LLM_PROVIDER
        logger.debug("llm_generate_call", provider=provider, prompt_length=len(prompt))

        if provider == "openai":
            return await self._generate_openai(prompt, system_prompt, temperature, max_tokens)
        elif provider == "anthropic":
            return await self._generate_anthropic(prompt, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    async def _generate_openai(
        self, prompt: str, system: str | None, temperature: float | None, max_tokens: int | None
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.openai.chat.completions.create(
            model=self.config.OPENAI_MODEL,
            messages=messages,
            temperature=temperature or self.config.OPENAI_TEMPERATURE,
            max_tokens=max_tokens or self.config.OPENAI_MAX_TOKENS,
        )
        return response.choices[0].message.content or ""

    async def _generate_anthropic(
        self, prompt: str, system: str | None, temperature: float | None, max_tokens: int | None
    ) -> str:
        response = await self.anthropic.messages.create(
            model=self.config.ANTHROPIC_MODEL,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature or self.config.OPENAI_TEMPERATURE,
            max_tokens=max_tokens or self.config.OPENAI_MAX_TOKENS,
        )
        return response.content[0].text if response.content else ""
