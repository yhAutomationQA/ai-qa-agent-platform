from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.test_runs import TestRun, RunStatus
from app.schemas.runs import RunCreate, RunStatusUpdate
from app.core.exceptions import NotFoundError


class RunService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def list_runs(self, skip: int = 0, limit: int = 100) -> List[TestRun]:
        result = await self.db.execute(
            select(TestRun).offset(skip).limit(limit).order_by(TestRun.created_at.desc())
        )
        return result.scalars().all()

    async def get_run(self, run_id: str) -> TestRun:
        result = await self.db.execute(select(TestRun).where(TestRun.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise NotFoundError("TestRun", run_id)
        return run

    async def create_run(self, payload: RunCreate) -> TestRun:
        run = TestRun(**payload.model_dump())
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def update_run_status(self, run_id: str, payload: RunStatusUpdate) -> TestRun:
        run = await self.get_run(run_id)
        run.status = RunStatus(payload.status)
        if payload.status in ("running",):
            run.started_at = datetime.now(timezone.utc)
        if payload.status in ("passed", "failed", "error", "cancelled", "timeout"):
            run.completed_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def cancel_run(self, run_id: str) -> TestRun:
        run = await self.get_run(run_id)
        if run.status in (RunStatus.PENDING, RunStatus.QUEUED, RunStatus.RUNNING):
            run.status = RunStatus.CANCELLED
            run.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(run)
        return run
