import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
import enum


class AgentStatus(str, enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"


class AgentType(str, enum.Enum):
    BROWSER = "browser"
    API = "api"
    PLANNER = "planner"
    REPORTER = "reporter"
    ORCHESTRATOR = "orchestrator"


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_type: Mapped[AgentType] = mapped_column(
        SAEnum(AgentType), nullable=False, default=AgentType.BROWSER
    )
    status: Mapped[AgentStatus] = mapped_column(
        SAEnum(AgentStatus), nullable=False, default=AgentStatus.IDLE
    )
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
