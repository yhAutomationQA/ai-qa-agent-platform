from pydantic_settings import BaseSettings, SettingsConfigDict


class AIConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Provider ───────────────────────────
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 4096

    # ── OpenAI ─────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.2
    OPENAI_MAX_TOKENS: int = 4096

    # ── Anthropic ──────────────────────────
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_TEMPERATURE: float = 0.2
    ANTHROPIC_MAX_TOKENS: int = 4096

    # ── Azure OpenAI ───────────────────────
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""

    # ── Retry ──────────────────────────────
    LLM_RETRY_MAX_ATTEMPTS: int = 3
    LLM_RETRY_BACKOFF_FACTOR: float = 2.0
    LLM_RETRY_MIN_WAIT: float = 1.0
    LLM_RETRY_MAX_WAIT: float = 30.0

    # ── Rate limiting ──────────────────────
    LLM_RATE_LIMIT_RPM: int = 60
    LLM_CONCURRENT_LIMIT: int = 5

    # ── Tokens ─────────────────────────────
    LLM_TOKEN_LIMIT: int = 128_000
    LLM_OUTPUT_TOKEN_LIMIT: int = 4096
    ENABLE_TOKEN_TRACKING: bool = True
    TOKEN_LOG_PATH: str = "logs/token_usage.jsonl"

    # ── Logging ────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"


ai_config = AIConfig()
