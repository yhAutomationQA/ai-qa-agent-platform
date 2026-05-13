from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime
import uuid
from enum import Enum


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class ExecutionLog(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = "INFO"
    source: str = "system"
    message: str = ""


class ExecutionArtifact(BaseModel):
    name: str
    path: str
    type: Literal["screenshot", "log", "report", "video", "trace", "other"] = "other"
    size_bytes: int | None = None
    captured_at: datetime = Field(default_factory=datetime.utcnow)


class TestStepResult(BaseModel):
    __test__ = False
    step_name: str
    status: StepStatus = StepStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None
    error_message: str | None = None
    assertion_details: dict[str, Any] | None = None
    screenshot_path: str | None = None
    logs: list[ExecutionLog] = Field(default_factory=list)


class TestSuiteResult(BaseModel):
    __test__ = False
    suite_name: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    error: int = 0
    duration_ms: float | None = None
    steps: list[TestStepResult] = Field(default_factory=list)


class ExecutionSummary(BaseModel):
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    error: int = 0
    total_duration_ms: float = 0.0
    start_time: datetime | None = None
    end_time: datetime | None = None
    suite_results: list[TestSuiteResult] = Field(default_factory=list)
    retries_used: int = 0
    max_retries: int = 0


class ExecutionType(str, Enum):
    PLAYWRIGHT = "playwright"
    API = "api"


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TestExecution(BaseModel):
    __test__ = False
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_case_id: str = ""
    test_case_name: str = ""
    execution_type: ExecutionType = ExecutionType.PLAYWRIGHT
    status: ExecutionStatus = ExecutionStatus.QUEUED
    attempt: int = 1
    max_retries: int = 0
    config: dict[str, Any] = Field(default_factory=dict)
    script: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None
    summary: ExecutionSummary = Field(default_factory=ExecutionSummary)
    artifacts: list[ExecutionArtifact] = Field(default_factory=list)
    logs: list[ExecutionLog] = Field(default_factory=list)
    error_message: str | None = None
    result_data: dict[str, Any] | None = None
