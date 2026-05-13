from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
import uuid


class ConfigCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    value: dict[str, Any]
    description: str | None = None
    environment: str = "development"


class ConfigUpdate(BaseModel):
    value: dict[str, Any] | None = None
    description: str | None = None
    environment: str | None = None


class ConfigResponse(BaseModel):
    id: uuid.UUID
    key: str
    value: dict[str, Any]
    description: str | None
    environment: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
