from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
import uuid


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    agent_type: str = "browser"
    config: dict[str, Any] | None = None


class AgentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    config: dict[str, Any] | None = None
    status: str | None = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    agent_type: str
    status: str
    config: dict[str, Any] | None
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
