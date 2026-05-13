from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
import uuid


class RunCreate(BaseModel):
    test_case_id: str
    agent_id: str | None = None
    parameters: dict[str, Any] | None = None


class RunStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|queued|running|passed|failed|error|cancelled|timeout)$")


class RunResponse(BaseModel):
    id: uuid.UUID
    test_case_id: uuid.UUID
    agent_id: uuid.UUID | None
    status: str
    result: dict[str, Any] | None
    artifacts: dict[str, Any] | None
    duration_ms: float | None
    error_message: str | None
    retry_count: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
