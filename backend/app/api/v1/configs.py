from fastapi import APIRouter, Depends
from typing import List

from app.schemas.configs import ConfigCreate, ConfigResponse, ConfigUpdate
from app.services.configs import ConfigService

router = APIRouter()


@router.get("/", response_model=List[ConfigResponse])
async def list_configs(
    service: ConfigService = Depends(),
):
    return await service.list_configs()


@router.get("/{config_key}", response_model=ConfigResponse)
async def get_config(
    config_key: str,
    service: ConfigService = Depends(),
):
    return await service.get_config(config_key)


@router.put("/{config_key}", response_model=ConfigResponse)
async def upsert_config(
    config_key: str,
    payload: ConfigUpdate,
    service: ConfigService = Depends(),
):
    return await service.upsert_config(config_key, payload)


@router.delete("/{config_key}", status_code=204)
async def delete_config(
    config_key: str,
    service: ConfigService = Depends(),
):
    return await service.delete_config(config_key)


@router.post("/reload")
async def reload_configs(
    service: ConfigService = Depends(),
):
    return await service.reload_configs()
