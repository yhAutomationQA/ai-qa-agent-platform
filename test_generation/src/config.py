from pydantic_settings import BaseSettings


class TestGenConfig(BaseSettings):
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 4096
    ENABLE_TOKEN_TRACKING: bool = True

    PLAYWRIGHT_VERSION: str = "^1.45.0"
    DEFAULT_TIMEOUT: int = 30000
    DEFAULT_VIEWPORT_WIDTH: int = 1280
    DEFAULT_VIEWPORT_HEIGHT: int = 720

    class Config:
        env_prefix = "TESTGEN_"
        case_sensitive = False


config = TestGenConfig()
