from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
import uuid


class TestCaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    test_type: str = "ui"
    agent_id: str | None = None
    script: str | None = None
    parameters: dict[str, Any] | None = None
    tags: list[str] | None = None


class TestCaseUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    test_type: str | None = None
    agent_id: str | None = None
    script: str | None = None
    parameters: dict[str, Any] | None = None
    tags: list[str] | None = None


class TestCaseResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    test_type: str
    agent_id: uuid.UUID | None
    script: str | None
    parameters: dict[str, Any] | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
