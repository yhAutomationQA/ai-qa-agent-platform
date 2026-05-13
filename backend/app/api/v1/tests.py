from fastapi import APIRouter, Depends, Query
from typing import List

from app.schemas.tests import TestCaseCreate, TestCaseResponse, TestCaseUpdate
from app.services.tests import TestCaseService

router = APIRouter()


@router.get("/", response_model=List[TestCaseResponse])
async def list_test_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: TestCaseService = Depends(),
):
    return await service.list_test_cases(skip=skip, limit=limit)


@router.post("/", response_model=TestCaseResponse, status_code=201)
async def create_test_case(
    payload: TestCaseCreate,
    service: TestCaseService = Depends(),
):
    return await service.create_test_case(payload)


@router.get("/{test_id}", response_model=TestCaseResponse)
async def get_test_case(
    test_id: str,
    service: TestCaseService = Depends(),
):
    return await service.get_test_case(test_id)


@router.patch("/{test_id}", response_model=TestCaseResponse)
async def update_test_case(
    test_id: str,
    payload: TestCaseUpdate,
    service: TestCaseService = Depends(),
):
    return await service.update_test_case(test_id, payload)


@router.delete("/{test_id}", status_code=204)
async def delete_test_case(
    test_id: str,
    service: TestCaseService = Depends(),
):
    return await service.delete_test_case(test_id)
