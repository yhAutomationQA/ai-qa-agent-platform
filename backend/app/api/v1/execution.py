from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Any

from app.execution.runner import TestExecutionEngine
from app.execution.models import (
    TestExecution,
    ExecutionType,
    ExecutionStatus,
)
from app.execution.config import ExecutionConfig
from app.execution.storage import ExecutionStorage
from pydantic import BaseModel, Field

router = APIRouter()


class ExecuteTestRequest(BaseModel):
    test_case_id: str
    test_case_name: str
    execution_type: str = Field(default="playwright", pattern="^(playwright|api)$")
    script: str | None = None
    test_file: str | None = None
    parameters: dict[str, Any] | None = None
    tags: list[str] | None = None
    max_retries: int = Field(default=0, ge=0, le=10)
    extra_args: list[str] | None = None


class BatchExecuteRequest(BaseModel):
    tests: list[ExecuteTestRequest]
    max_parallel: int = Field(default=4, ge=1, le=32)


engine = TestExecutionEngine()


@router.post("/execute", response_model=TestExecution)
async def execute_test(payload: ExecuteTestRequest):
    execution = engine.create_execution(
        test_case_id=payload.test_case_id,
        test_case_name=payload.test_case_name,
        execution_type=ExecutionType(payload.execution_type),
        script=payload.script,
        parameters=payload.parameters,
        tags=payload.tags,
        max_retries=payload.max_retries,
    )
    result = await engine.execute(
        execution,
        test_file=payload.test_file,
        extra_args=payload.extra_args,
    )
    return result


@router.post("/execute/batch", response_model=list[TestExecution])
async def execute_batch(payload: BatchExecuteRequest):
    engine.config.max_parallel_workers = payload.max_parallel
    executions = []
    test_files = {}

    for t in payload.tests:
        ex = engine.create_execution(
            test_case_id=t.test_case_id,
            test_case_name=t.test_case_name,
            execution_type=ExecutionType(t.execution_type),
            script=t.script,
            parameters=t.parameters,
            tags=t.tags,
            max_retries=t.max_retries,
        )
        executions.append(ex)
        if t.test_file:
            test_files[ex.id] = t.test_file

    results = await engine.execute_batch(
        executions,
        test_files=test_files if test_files else None,
    )
    return results


@router.post("/execute/{test_type}", response_model=TestExecution)
async def execute_playwright_test(
    test_type: str,
    test_file: str = Query(..., description="Path to test file"),
    test_case_id: str = Query("manual", description="Test case identifier"),
    max_retries: int = Query(0, ge=0, le=10),
):
    if test_type not in ("playwright", "api"):
        raise HTTPException(status_code=400, detail="test_type must be 'playwright' or 'api'")

    execution = engine.create_execution(
        test_case_id=test_case_id,
        test_case_name=f"Manual {test_type} run: {test_file}",
        execution_type=ExecutionType(test_type),
        max_retries=max_retries,
    )
    result = await engine.execute(execution, test_file=test_file)
    return result


@router.get("/config", response_model=ExecutionConfig)
async def get_execution_config():
    return engine.config


@router.put("/config", response_model=ExecutionConfig)
async def update_execution_config(new_config: ExecutionConfig):
    engine.config = new_config
    engine.storage = ExecutionStorage(new_config.artifact_dir)
    return engine.config
