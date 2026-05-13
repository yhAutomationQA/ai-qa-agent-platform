class AIOrchestratorError(Exception):
    pass


class AIServiceError(AIOrchestratorError):
    def __init__(self, message: str, provider: str | None = None, status_code: int | None = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(message)


class ProviderNotAvailableError(AIServiceError):
    def __init__(self, provider: str):
        super().__init__(f"Provider '{provider}' is not available", provider=provider)


class RateLimitError(AIServiceError):
    def __init__(self, provider: str, retry_after: float | None = None):
        self.retry_after = retry_after
        super().__init__("Rate limit exceeded", provider=provider, status_code=429)


class TokenLimitError(AIServiceError):
    def __init__(self, prompt_tokens: int, max_tokens: int, provider: str | None = None):
        self.prompt_tokens = prompt_tokens
        self.max_tokens = max_tokens
        super().__init__(
            f"Prompt exceeds token limit ({prompt_tokens} > {max_tokens})",
            provider=provider,
            status_code=413,
        )


class InvalidResponseError(AIOrchestratorError):
    def __init__(self, raw: str, reason: str = "Failed to parse"):
        self.raw = raw
        super().__init__(f"{reason}: {raw[:200]}")


class ContextBuildError(AIOrchestratorError):
    pass


class PromptTemplateError(AIOrchestratorError):
    pass


class ConfigurationError(AIOrchestratorError):
    pass
