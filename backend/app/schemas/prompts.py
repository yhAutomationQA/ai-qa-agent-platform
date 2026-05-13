from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
import uuid


class PromptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    template: str
    variables: list[str] | None = None
    tags: list[str] | None = None
    change_log: str | None = None


class PromptUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    template: str | None = None
    variables: list[str] | None = None
    status: str | None = None
    tags: list[str] | None = None


class PromptResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    template: str
    variables: list[str] | None
    status: str
    version: int
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
