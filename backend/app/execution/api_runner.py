import asyncio
import os
from datetime import datetime
from typing import Any

from app.execution.config import ExecutionConfig
from app.execution.models import (
    TestExecution,
    ExecutionStatus,
)
from app.execution.log_capture import LogCapture
from app.execution.result_parser import ResultParser
from app.execution.storage import ExecutionStorage
from app.execution.summary import SummaryGenerator


class ApiTestRunner:
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
        test_path: str | None = None,
        pytest_args: list[str] | None = None,
    ) -> TestExecution:
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.utcnow()
        log_capture = LogCapture(max_bytes=self.config.log_max_bytes)
        report_path = self.storage._run_dir(execution.id) / "api-results.xml"

        log_capture.add(f"Starting API test execution: {execution.test_case_name}", level="INFO")
        log_capture.add(f"Test path: {test_path or 'N/A'}", level="INFO")
        log_capture.add_separator()

        cmd = self._build_command(execution, test_path, pytest_args, report_path)
        log_capture.add(f"Command: {' '.join(cmd)}", level="DEBUG")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ},
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
            execution.error_message = "pytest not found. Ensure it is installed."
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

        self._parse_results(execution, log_capture, report_path)

        if execution.status not in (ExecutionStatus.TIMEOUT, ExecutionStatus.ERROR):
            execution.status = (
                ExecutionStatus.PASSED if exit_code == 0 else ExecutionStatus.FAILED
            )

        execution.logs = log_capture.logs
        artifact = self.storage.save_log(execution.id, log_capture.raw_text)
        execution.artifacts.append(artifact)

        execution.summary = SummaryGenerator.from_execution(execution)

        return execution

    def _build_command(
        self,
        execution: TestExecution,
        test_path: str | None,
        pytest_args: list[str] | None,
        report_path: str,
    ) -> list[str]:
        cmd = ["python", "-m", "pytest"]

        if test_path:
            cmd.append(test_path)
        elif execution.script:
            tmpfile = self.storage._run_dir(execution.id) / "api_test_script.py"
            tmpfile.write_text(execution.script)
            cmd.append(str(tmpfile))

        cmd.extend([
            f"--junitxml={report_path}",
        ])

        base_args = pytest_args or self.config.pytest_args
        cmd.extend(base_args)

        return cmd

    def _parse_results(
        self,
        execution: TestExecution,
        log_capture: LogCapture,
        report_path: str,
    ) -> None:
        if os.path.exists(report_path):
            log_capture.add("Found JUnit XML report, parsing results", level="DEBUG")
            try:
                with open(report_path) as f:
                    xml_content = f.read()
                suites = ResultParser.parse_junit_xml(xml_content)
                execution.summary = SummaryGenerator.from_suite_results(suites)

                for suite in suites:
                    for step in suite.steps:
                        log_capture.add(
                            f"  [{step.status.value.upper()}] {step.step_name} "
                            f"({step.duration_ms or 0:.0f} ms)",
                            level="INFO",
                        )
            except Exception as e:
                log_capture.add(f"Failed to parse JUnit XML: {e}", level="WARNING")
