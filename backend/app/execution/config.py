from pydantic import BaseModel, Field
from typing import Literal


class ExecutionConfig(BaseModel):
    max_retries: int = Field(default=3, ge=0, description="Max retries per test")
    retry_delay_seconds: float = Field(default=2.0, ge=0, description="Delay between retries")
    timeout_seconds: int = Field(default=300, ge=1, description="Per-test timeout")
    max_parallel_workers: int = Field(default=4, ge=1, le=32, description="Parallel execution limit")
    artifact_dir: str = Field(default=".execution_artifacts", description="Artifact output directory")
    playwright_binary: str = Field(default="npx playwright", description="Playwright CLI command")
    pytest_args: list[str] = Field(
        default=["-v", "--tb=short", "--no-header"],
        description="Default pytest arguments for API tests",
    )
    report_format: Literal["junit", "json"] = Field(
        default="junit", description="Test report format"
    )
    screenshot_on_failure: bool = Field(default=True, description="Capture screenshot on failure")
    capture_stdout: bool = Field(default=True, description="Capture stdout from subprocess")
    capture_stderr: bool = Field(default=True, description="Capture stderr from subprocess")
    log_max_bytes: int = Field(default=10_485_760, description="Max log size per run (10MB)")
    jupiter_timeout_seconds: int = Field(default=60, ge=1, description="Timeout for Jupiter API tests")
