import structlog
import tiktoken

from openai import AsyncOpenAI

from ai_orchestrator.llm.base import LLMProvider
from ai_orchestrator.models import LLMResponse, TokenUsage
from ai_orchestrator.config import ai_config
from ai_orchestrator.exceptions import (
    AIServiceError,
    RateLimitError,
    TokenLimitError,
)

logger = structlog.get_logger()


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self._client: AsyncOpenAI | None = None
        self._model = ai_config.OPENAI_MODEL
        self._encoding = tiktoken.encoding_for_model(self._model)

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            if not ai_config.OPENAI_API_KEY:
                raise AIServiceError("OPENAI_API_KEY is not configured", provider="openai")
            self._client = AsyncOpenAI(api_key=ai_config.OPENAI_API_KEY)
        return self._client

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "openai"

    def count_tokens(self, text: str) -> int:
        return len(self._encoding.encode(text))

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        prompt_tokens = self.count_tokens(prompt) + (self.count_tokens(system_prompt or ""))

        if prompt_tokens > ai_config.LLM_TOKEN_LIMIT:
            raise TokenLimitError(prompt_tokens, ai_config.LLM_TOKEN_LIMIT, provider="openai")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature or ai_config.OPENAI_TEMPERATURE,
                max_tokens=max_tokens or ai_config.OPENAI_MAX_TOKENS,
            )
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str:
                raise RateLimitError("openai")
            raise AIServiceError(str(e), provider="openai")

        choice = response.choices[0]
        usage = response.usage

        token_usage = None
        if usage:
            token_usage = TokenUsage(
                prompt_tokens=usage.prompt_tokens or 0,
                completion_tokens=usage.completion_tokens or 0,
                total_tokens=usage.total_tokens or 0,
                model=self._model,
                provider="openai",
            )

        return LLMResponse(
            content=choice.message.content or "",
            token_usage=token_usage,
            finish_reason=choice.finish_reason or "",
            raw_response=response,
        )
