from pydantic_settings import BaseSettings, SettingsConfigDict


class OrchestratorConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.2
    OPENAI_MAX_TOKENS: int = 4096

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    LLM_PROVIDER: str = "openai"
    LLM_RATE_LIMIT_RPM: int = 60
    LLM_RETRY_MAX_ATTEMPTS: int = 3
    LLM_RETRY_BACKOFF_FACTOR: float = 2.0

    EMBEDDING_MODEL: str = "text-embedding-3-small"
    REDIS_URL: str = "redis://localhost:6379/0"
    LOG_LEVEL: str = "INFO"
