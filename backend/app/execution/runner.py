import asyncio
from datetime import datetime, timezone
from typing import Any

from app.execution.config import ExecutionConfig
from app.execution.models import (
    TestExecution,
    ExecutionStatus,
    ExecutionType,
    ExecutionSummary,
)
from app.execution.playwright_runner import PlaywrightRunner
from app.execution.api_runner import ApiTestRunner
from app.execution.storage import ExecutionStorage
from app.execution.log_capture import LogCapture
from app.execution.summary import SummaryGenerator


class TestExecutionEngine:
    def __init__(self, config: ExecutionConfig | None = None):
        self.config = config or ExecutionConfig()
        self.storage = ExecutionStorage(self.config.artifact_dir)
        self.playwright_runner = PlaywrightRunner(self.config, self.storage)
        self.api_runner = ApiTestRunner(self.config, self.storage)

    async def execute(
        self,
        execution: TestExecution,
        test_file: str | None = None,
        extra_args: list[str] | None = None,
        pytest_args: list[str] | None = None,
    ) -> TestExecution:
        max_retries = execution.max_retries or self.config.max_retries
        attempt = 0

        while attempt <= max_retries:
            attempt += 1
            execution.attempt = attempt

            if execution.execution_type == ExecutionType.PLAYWRIGHT:
                execution = await self.playwright_runner.run(
                    execution,
                    test_file=test_file,
                    extra_args=extra_args,
                )
            elif execution.execution_type == ExecutionType.API:
                execution = await self.api_runner.run(
                    execution,
                    test_path=test_file,
                    pytest_args=pytest_args,
                )

            if execution.status in (ExecutionStatus.PASSED, ExecutionStatus.CANCELLED):
                execution.summary.retries_used = attempt - 1
                execution.summary.max_retries = max_retries
                return execution

            if attempt <= max_retries:
                delay = self._backoff_delay(attempt)
                execution.logs.append(
                    f"Attempt {attempt}/{max_retries + 1} failed. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)

                execution.status = ExecutionStatus.QUEUED
                execution.error_message = None
                execution.summary = ExecutionSummary()

        execution.summary.retries_used = max_retries
        execution.summary.max_retries = max_retries

        return execution

    async def execute_batch(
        self,
        executions: list[TestExecution],
        test_files: dict[str, str] | None = None,
        extra_args: list[str] | None = None,
        pytest_args: list[str] | None = None,
    ) -> list[TestExecution]:
        semaphore = asyncio.Semaphore(self.config.max_parallel_workers)

        async def _run_with_semaphore(ex: TestExecution) -> TestExecution:
            async with semaphore:
                test_file = None
                if test_files:
                    test_file = test_files.get(ex.id)
                return await self.execute(
                    ex,
                    test_file=test_file,
                    extra_args=extra_args,
                    pytest_args=pytest_args,
                )

        tasks = [_run_with_semaphore(ex) for ex in executions]
        return await asyncio.gather(*tasks)

    async def execute_with_timeout(
        self,
        execution: TestExecution,
        timeout_seconds: int | None = None,
        **kwargs: Any,
    ) -> TestExecution:
        timeout = timeout_seconds or self.config.timeout_seconds
        try:
            return await asyncio.wait_for(
                self.execute(execution, **kwargs),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            execution.status = ExecutionStatus.TIMEOUT
            execution.completed_at = datetime.now(timezone.utc)
            execution.error_message = f"Timed out after {timeout}s"
            return execution

    @staticmethod
    def _backoff_delay(attempt: int, base_delay: float = 2.0) -> float:
        delay = base_delay * (2 ** (attempt - 1))
        return min(delay, 60.0)

    @staticmethod
    def create_execution(
        test_case_id: str,
        test_case_name: str,
        execution_type: ExecutionType,
        script: str | None = None,
        parameters: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        max_retries: int = 0,
    ) -> TestExecution:
        return TestExecution(
            test_case_id=test_case_id,
            test_case_name=test_case_name,
            execution_type=execution_type,
            script=script,
            parameters=parameters or {},
            tags=tags or [],
            max_retries=max_retries,
        )
