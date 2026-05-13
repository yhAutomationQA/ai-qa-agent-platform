from fastapi import APIRouter, Depends, Query
from typing import List

from app.schemas.agents import AgentCreate, AgentResponse, AgentUpdate
from app.services.agents import AgentService

router = APIRouter()


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: AgentService = Depends(),
):
    return await service.list_agents(skip=skip, limit=limit)


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(
    payload: AgentCreate,
    service: AgentService = Depends(),
):
    return await service.create_agent(payload)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    service: AgentService = Depends(),
):
    return await service.get_agent(agent_id)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    service: AgentService = Depends(),
):
    return await service.update_agent(agent_id, payload)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    service: AgentService = Depends(),
):
    return await service.delete_agent(agent_id)
