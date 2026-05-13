import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from app.execution.config import ExecutionConfig
from app.execution.models import (
    TestExecution,
    ExecutionStatus,
    ExecutionLog,
    ExecutionArtifact,
    StepStatus,
    TestStepResult,
    ExecutionSummary,
)
from app.execution.log_capture import LogCapture
from app.execution.result_parser import ResultParser
from app.execution.storage import ExecutionStorage
from app.execution.summary import SummaryGenerator


class PlaywrightRunner:
    def __init__(
        self,
        config: ExecutionConfig | None = None,
        storage: ExecutionStorage | None = None,
    ):
        self.config = config or ExecutionConfig()
        self.storage = storage or ExecutionStorage(self.config.artifact_dir)

    async def run(
        self,
        execution: TestExecution,
        test_file: str | None = None,
        extra_args: list[str] | None = None,
    ) -> TestExecution:
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.utcnow()
        log_capture = LogCapture(max_bytes=self.config.log_max_bytes)

        log_capture.add(f"Starting Playwright execution: {execution.test_case_name}", level="INFO")
        log_capture.add(f"Test file: {test_file or 'N/A'}", level="INFO")
        log_capture.add_separator()

        cmd = self._build_command(execution, test_file, extra_args)
        log_capture.add(f"Command: {' '.join(cmd)}", level="DEBUG")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PLAYWRIGHT_JSON_OUTPUT_NAME": str(
                    self.storage._run_dir(execution.id) / "playwright-report.json"
                )},
            )

            stdout_task = asyncio.create_task(
                log_capture.capture_stream(proc.stdout, source="stdout", level="INFO")
            )
            stderr_task = asyncio.create_task(
                log_capture.capture_stream(proc.stderr, source="stderr", level="ERROR")
            )

            try:
                exit_code = await asyncio.wait_for(
                    proc.wait(), timeout=self.config.timeout_seconds
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                execution.status = ExecutionStatus.TIMEOUT
                execution.error_message = (
                    f"Timed out after {self.config.timeout_seconds}s"
                )
                log_capture.add(
                    f"Execution timed out ({self.config.timeout_seconds}s)", level="ERROR"
                )
                exit_code = -1

            await stdout_task
            await stderr_task

        except FileNotFoundError:
            execution.status = ExecutionStatus.ERROR
            execution.error_message = (
                f"Playwright binary not found: {self.config.playwright_binary}"
            )
            log_capture.add(execution.error_message, level="ERROR")
            exit_code = -1
        except Exception as e:
            execution.status = ExecutionStatus.ERROR
            execution.error_message = str(e)
            log_capture.add(f"Execution error: {e}", level="ERROR")
            exit_code = -1

        execution.completed_at = datetime.utcnow()
        execution.duration_ms = (
            (execution.completed_at - execution.started_at).total_seconds() * 1000
        )

        log_capture.add_separator()
        log_capture.add(f"Exit code: {exit_code}", level="INFO")
        log_capture.add(f"Duration: {execution.duration_ms:.0f} ms", level="INFO")

        self._parse_playwright_results(execution, log_capture)

        if execution.status not in (ExecutionStatus.TIMEOUT, ExecutionStatus.ERROR):
            execution.status = (
                ExecutionStatus.PASSED if exit_code == 0 else ExecutionStatus.FAILED
            )

        execution.logs = log_capture.logs

        artifact = self.storage.save_log(execution.id, log_capture.raw_text)
        execution.artifacts.append(artifact)

        self._discover_artifacts(execution)

        execution.summary = SummaryGenerator.from_execution(execution)

        return execution

    def _build_command(
        self,
        execution: TestExecution,
        test_file: str | None,
        extra_args: list[str] | None,
    ) -> list[str]:
        cmd_parts = self.config.playwright_binary.split()
        cmd = cmd_parts + ["test"]

        if test_file:
            cmd.append(test_file)
        elif execution.script:
            tmp_file = self.storage._run_dir(execution.id) / "playwright_test.spec.ts"
            tmp_file.write_text(execution.script)
            cmd.append(str(tmp_file))

        cmd.extend(["--reporter", "json,html"])

        if extra_args:
            cmd.extend(extra_args)

        return cmd

    def _parse_playwright_results(
        self,
        execution: TestExecution,
        log_capture: LogCapture,
    ) -> None:
        report_path = self.storage._run_dir(execution.id) / "playwright-report.json"
        if report_path.exists():
            log_capture.add("Found Playwright JSON report, parsing results", level="DEBUG")
            suites = ResultParser.parse_playwright_json(str(report_path))
            execution.summary = SummaryGenerator.from_suite_results(suites)

            for suite in suites:
                for step in suite.steps:
                    log_capture.add(
                        f"  [{step.status.value.upper()}] {step.step_name} "
                        f"({step.duration_ms or 0:.0f} ms)",
                        level="INFO",
                    )

    def _discover_artifacts(self, execution: TestExecution) -> None:
        existing = self.storage.list_artifacts(execution.id)
        for art in existing:
            if art.name not in [a.name for a in execution.artifacts]:
                execution.artifacts.append(art)
