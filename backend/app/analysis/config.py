from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnalysisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ANALYSIS_ENABLE_AI: bool = True
    ANALYSIS_AI_FALLBACK: bool = True
    ANALYSIS_CONFIDENCE_THRESHOLD: float = Field(default=0.6, ge=0.0, le=1.0)
    ANALYSIS_MAX_INPUT_LENGTH: int = Field(default=50_000, description="Max chars for LLM input")
    ANALYSIS_MAX_SUMMARIES: int = Field(default=20, description="Max failures in one batch analysis")
    ANALYSIS_SCREENSHOT_ENABLED: bool = True
    ANALYSIS_SCREENSHOT_MAX_SIZE: int = Field(
        default=5_000_000, description="Max bytes for screenshot upload"
    )


analysis_settings = AnalysisSettings()
