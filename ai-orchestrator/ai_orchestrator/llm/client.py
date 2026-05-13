import structlog
from typing import Any

from ai_orchestrator.llm.base import LLMProvider
from ai_orchestrator.llm.openai_provider import OpenAIProvider
from ai_orchestrator.llm.anthropic_provider import AnthropicProvider
from ai_orchestrator.models import LLMResponse
from ai_orchestrator.core.retry import RetryHandler
from ai_orchestrator.core.token_tracker import TokenTracker
from ai_orchestrator.config import ai_config
from ai_orchestrator.exceptions import ConfigurationError

logger = structlog.get_logger()


_providers: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


class LLMClient:
    def __init__(
        self,
        provider: str | None = None,
        token_tracker: TokenTracker | None = None,
        retry_handler: RetryHandler | None = None,
    ):
        provider_name = provider or ai_config.LLM_PROVIDER
        provider_class = _providers.get(provider_name)
        if not provider_class:
            raise ConfigurationError(
                f"Unknown LLM provider '{provider_name}'. Available: {list(_providers.keys())}"
            )
        self._provider = provider_class()
        self.token_tracker = token_tracker or TokenTracker()
        self.retry_handler = retry_handler or RetryHandler()

    @property
    def provider(self) -> LLMProvider:
        return self._provider

    @property
    def model_name(self) -> str:
        return self._provider.model_name

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        track_usage: bool = True,
    ) -> LLMResponse:
        logger.debug(
            "llm_generate",
            provider=self._provider.provider_name,
            model=self._provider.model_name,
            prompt_length=len(prompt),
        )

        response = await self.retry_handler.execute(
            self._provider.generate,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if track_usage and response.token_usage and ai_config.ENABLE_TOKEN_TRACKING:
            self.token_tracker.track(
                prompt_tokens=response.token_usage.prompt_tokens,
                completion_tokens=response.token_usage.completion_tokens,
                model=self._provider.model_name,
                provider=self._provider.provider_name,
            )

        logger.info(
            "llm_response_received",
            finish_reason=response.finish_reason,
            content_length=len(response.content),
            tokens=response.token_usage.total_tokens if response.token_usage else None,
        )

        return response

    def count_tokens(self, text: str) -> int:
        return self._provider.count_tokens(text)

    def session_summary(self) -> dict:
        return self.token_tracker.session_summary()
