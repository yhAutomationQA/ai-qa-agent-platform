from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.test_cases import TestCase
from app.schemas.tests import TestCaseCreate, TestCaseUpdate
from app.core.exceptions import NotFoundError


class TestCaseService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def list_test_cases(self, skip: int = 0, limit: int = 100) -> List[TestCase]:
        result = await self.db.execute(
            select(TestCase).offset(skip).limit(limit).order_by(TestCase.created_at.desc())
        )
        return result.scalars().all()

    async def get_test_case(self, test_id: str) -> TestCase:
        result = await self.db.execute(select(TestCase).where(TestCase.id == test_id))
        test_case = result.scalar_one_or_none()
        if not test_case:
            raise NotFoundError("TestCase", test_id)
        return test_case

    async def create_test_case(self, payload: TestCaseCreate) -> TestCase:
        test_case = TestCase(**payload.model_dump())
        self.db.add(test_case)
        await self.db.flush()
        await self.db.refresh(test_case)
        return test_case

    async def update_test_case(self, test_id: str, payload: TestCaseUpdate) -> TestCase:
        test_case = await self.get_test_case(test_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(test_case, field, value)
        await self.db.flush()
        await self.db.refresh(test_case)
        return test_case

    async def delete_test_case(self, test_id: str) -> None:
        test_case = await self.get_test_case(test_id)
        await self.db.delete(test_case)
        await self.db.flush()
