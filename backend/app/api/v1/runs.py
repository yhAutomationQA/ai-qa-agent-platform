from fastapi import APIRouter, Depends, Query
from typing import List

from app.schemas.runs import RunCreate, RunResponse, RunStatusUpdate
from app.services.runs import RunService

router = APIRouter()


@router.get("/", response_model=List[RunResponse])
async def list_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: RunService = Depends(),
):
    return await service.list_runs(skip=skip, limit=limit)


@router.post("/", response_model=RunResponse, status_code=201)
async def create_run(
    payload: RunCreate,
    service: RunService = Depends(),
):
    return await service.create_run(payload)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    service: RunService = Depends(),
):
    return await service.get_run(run_id)


@router.patch("/{run_id}/status", response_model=RunResponse)
async def update_run_status(
    run_id: str,
    payload: RunStatusUpdate,
    service: RunService = Depends(),
):
    return await service.update_run_status(run_id, payload)


@router.post("/{run_id}/cancel", response_model=RunResponse)
async def cancel_run(
    run_id: str,
    service: RunService = Depends(),
):
    return await service.cancel_run(run_id)
