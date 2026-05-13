import structlog

from anthropic import AsyncAnthropic

from ai_orchestrator.llm.base import LLMProvider
from ai_orchestrator.models import LLMResponse, TokenUsage
from ai_orchestrator.config import ai_config
from ai_orchestrator.exceptions import AIServiceError, RateLimitError

logger = structlog.get_logger()


class AnthropicProvider(LLMProvider):
    def __init__(self):
        self._client: AsyncAnthropic | None = None
        self._model = ai_config.ANTHROPIC_MODEL

    @property
    def client(self) -> AsyncAnthropic:
        if self._client is None:
            if not ai_config.ANTHROPIC_API_KEY:
                raise AIServiceError("ANTHROPIC_API_KEY is not configured", provider="anthropic")
            self._client = AsyncAnthropic(api_key=ai_config.ANTHROPIC_API_KEY)
        return self._client

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def count_tokens(self, text: str) -> int:
        return self.client.count_tokens(text) if self._client else len(text) // 4

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        try:
            response = await self.client.messages.create(
                model=self._model,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature or ai_config.ANTHROPIC_TEMPERATURE,
                max_tokens=max_tokens or ai_config.ANTHROPIC_MAX_TOKENS,
            )
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str:
                raise RateLimitError("anthropic")
            raise AIServiceError(str(e), provider="anthropic")

        token_usage = TokenUsage(
            prompt_tokens=response.usage.input_tokens if response.usage else 0,
            completion_tokens=response.usage.output_tokens if response.usage else 0,
            total_tokens=(
                (response.usage.input_tokens + response.usage.output_tokens)
                if response.usage
                else 0
            ),
            model=self._model,
            provider="anthropic",
        )

        content = ""
        if response.content:
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

        return LLMResponse(
            content=content,
            token_usage=token_usage,
            finish_reason=response.stop_reason or "",
            raw_response=response,
        )
