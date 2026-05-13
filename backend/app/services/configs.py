from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.configs import Config
from app.schemas.configs import ConfigCreate, ConfigUpdate
from app.core.exceptions import NotFoundError


class ConfigService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def list_configs(self) -> List[Config]:
        result = await self.db.execute(select(Config).order_by(Config.key))
        return result.scalars().all()

    async def get_config(self, config_key: str) -> Config:
        result = await self.db.execute(select(Config).where(Config.key == config_key))
        config = result.scalar_one_or_none()
        if not config:
            raise NotFoundError("Config", config_key)
        return config

    async def upsert_config(self, config_key: str, payload: ConfigUpdate) -> Config:
        result = await self.db.execute(select(Config).where(Config.key == config_key))
        config = result.scalar_one_or_none()
        if config:
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(config, field, value)
        else:
            config = Config(
                key=config_key,
                value=payload.value or {},
                description=payload.description,
                environment=payload.environment or "development",
            )
            self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def delete_config(self, config_key: str) -> None:
        config = await self.get_config(config_key)
        await self.db.delete(config)
        await self.db.flush()

    async def reload_configs(self) -> dict:
        return {"message": "Configuration reloaded successfully"}
