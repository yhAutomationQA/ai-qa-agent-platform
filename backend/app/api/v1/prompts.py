from fastapi import APIRouter, Depends, Query
from typing import List

from app.schemas.prompts import PromptCreate, PromptResponse, PromptUpdate
from app.services.prompts import PromptService

router = APIRouter()


@router.get("/", response_model=List[PromptResponse])
async def list_prompts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PromptService = Depends(),
):
    return await service.list_prompts(skip=skip, limit=limit)


@router.post("/", response_model=PromptResponse, status_code=201)
async def create_prompt(
    payload: PromptCreate,
    service: PromptService = Depends(),
):
    return await service.create_prompt(payload)


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: str,
    service: PromptService = Depends(),
):
    return await service.get_prompt(prompt_id)


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    payload: PromptUpdate,
    service: PromptService = Depends(),
):
    return await service.update_prompt(prompt_id, payload)


@router.post("/{prompt_id}/versions", response_model=PromptResponse)
async def create_prompt_version(
    prompt_id: str,
    payload: PromptCreate,
    service: PromptService = Depends(),
):
    return await service.create_version(prompt_id, payload)


@router.get("/{prompt_id}/versions", response_model=List[PromptResponse])
async def list_prompt_versions(
    prompt_id: str,
    service: PromptService = Depends(),
):
    return await service.list_versions(prompt_id)
