from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.agents import Agent
from app.schemas.agents import AgentCreate, AgentUpdate
from app.core.exceptions import NotFoundError


class AgentService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def list_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        result = await self.db.execute(
            select(Agent).offset(skip).limit(limit).order_by(Agent.created_at.desc())
        )
        return result.scalars().all()

    async def get_agent(self, agent_id: str) -> Agent:
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise NotFoundError("Agent", agent_id)
        return agent

    async def create_agent(self, payload: AgentCreate) -> Agent:
        agent = Agent(**payload.model_dump())
        self.db.add(agent)
        await self.db.flush()
        await self.db.refresh(agent)
        return agent

    async def update_agent(self, agent_id: str, payload: AgentUpdate) -> Agent:
        agent = await self.get_agent(agent_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(agent, field, value)
        await self.db.flush()
        await self.db.refresh(agent)
        return agent

    async def delete_agent(self, agent_id: str) -> None:
        agent = await self.get_agent(agent_id)
        await self.db.delete(agent)
        await self.db.flush()
