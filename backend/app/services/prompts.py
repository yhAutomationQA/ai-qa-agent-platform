from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.prompts import Prompt, PromptVersion
from app.schemas.prompts import PromptCreate, PromptUpdate
from app.core.exceptions import NotFoundError


class PromptService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def list_prompts(self, skip: int = 0, limit: int = 100) -> List[Prompt]:
        result = await self.db.execute(
            select(Prompt).offset(skip).limit(limit).order_by(Prompt.created_at.desc())
        )
        return result.scalars().all()

    async def get_prompt(self, prompt_id: str) -> Prompt:
        result = await self.db.execute(select(Prompt).where(Prompt.id == prompt_id))
        prompt = result.scalar_one_or_none()
        if not prompt:
            raise NotFoundError("Prompt", prompt_id)
        return prompt

    async def create_prompt(self, payload: PromptCreate) -> Prompt:
        prompt = Prompt(**payload.model_dump(exclude={"change_log"}))
        self.db.add(prompt)
        await self.db.flush()
        await self.db.refresh(prompt)
        return prompt

    async def update_prompt(self, prompt_id: str, payload: PromptUpdate) -> Prompt:
        prompt = await self.get_prompt(prompt_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(prompt, field, value)
        prompt.version += 1
        await self.db.flush()
        await self.db.refresh(prompt)
        return prompt

    async def create_version(self, prompt_id: str, payload: PromptCreate) -> Prompt:
        prompt = await self.get_prompt(prompt_id)
        version = PromptVersion(
            prompt_id=prompt.id,
            version=prompt.version,
            template=payload.template,
            variables=payload.variables,
            change_log=payload.change_log,
        )
        self.db.add(version)
        prompt.template = payload.template
        prompt.variables = payload.variables
        prompt.version += 1
        await self.db.flush()
        await self.db.refresh(prompt)
        return prompt

    async def list_versions(self, prompt_id: str) -> List[PromptVersion]:
        await self.get_prompt(prompt_id)
        result = await self.db.execute(
            select(PromptVersion)
            .where(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.version.desc())
        )
        return result.scalars().all()
