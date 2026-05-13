import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from app.execution.config import ExecutionConfig
from app.execution.models import (
    TestExecution,
    TestStepResult,
    ExecutionArtifact,
    ExecutionSummary,
    ExecutionLog,
    ExecutionType,
    ExecutionStatus,
    StepStatus,
    TestSuiteResult,
)
from app.execution.log_capture import LogCapture
from app.execution.result_parser import ResultParser
from app.execution.storage import ExecutionStorage
from app.execution.summary import SummaryGenerator


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def sample_execution():
    return TestExecution(
        id="test-exec-1",
        test_case_id="tc-1",
        test_case_name="Login Test",
        execution_type=ExecutionType.PLAYWRIGHT,
        script='test("login", async () => { /* ... */ });',
        parameters={"url": "https://example.com"},
        tags=["smoke", "login"],
        max_retries=2,
    )


@pytest.fixture
def sample_junit_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="LoginSuite" tests="3" failures="1" errors="0" skipped="1" time="2.5">
    <testcase classname="LoginSuite" name="test_valid_login" time="0.5"/>
    <testcase classname="LoginSuite" name="test_invalid_login" time="0.3">
      <failure message="Expected 200, got 401">Auth failed</failure>
    </testcase>
    <testcase classname="LoginSuite" name="test_logout" time="0.2">
      <skipped message="Not implemented yet"/>
    </testcase>
  </testsuite>
  <testsuite name="DashboardSuite" tests="2" failures="0" errors="0" skipped="0" time="1.0">
    <testcase classname="DashboardSuite" name="test_loads" time="0.6"/>
    <testcase classname="DashboardSuite" name="test_widgets" time="0.4"/>
  </testsuite>
</testsuites>"""


@pytest.fixture
def sample_playwright_json():
    return json.dumps([
        {
            "file": "login.spec.ts",
            "specs": [
                {
                    "title": "should login successfully",
                    "tests": [
                        {
                            "results": [
                                {
                                    "status": "expected",
                                    "duration": 500000,
                                    "error": None,
                                }
                            ]
                        }
                    ],
                },
                {
                    "title": "should show error on invalid credentials",
                    "tests": [
                        {
                            "results": [
                                {
                                    "status": "unexpected",
                                    "duration": 300000,
                                    "error": "TimeoutError: page.click() timed out",
                                }
                            ]
                        }
                    ],
                },
            ],
        }
    ])


@pytest.fixture
def sample_json_report():
    return json.dumps([
        {
            "name": "API Tests",
            "tests": [
                {
                    "title": "GET /users returns 200",
                    "status": "passed",
                    "duration_ms": 150.0,
                },
                {
                    "title": "POST /users validates email",
                    "status": "failed",
                    "duration_ms": 80.0,
                    "error": "AssertionError: 422 != 201",
                },
            ],
        }
    ])


@pytest.fixture
def tmp_artifact_dir(tmp_path):
    return str(tmp_path / "artifacts")


# ── Test ExecutionConfig ──────────────────────────────────

class TestExecutionConfig:
    def test_defaults(self):
        config = ExecutionConfig()
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 2.0
        assert config.timeout_seconds == 300
        assert config.max_parallel_workers == 4
        assert config.screenshot_on_failure is True

    def test_custom_values(self):
        config = ExecutionConfig(max_retries=5, timeout_seconds=600, max_parallel_workers=8)
        assert config.max_retries == 5
        assert config.timeout_seconds == 600
        assert config.max_parallel_workers == 8

    def test_max_parallel_clamp(self):
        with pytest.raises(Exception):
            ExecutionConfig(max_parallel_workers=0)
        with pytest.raises(Exception):
            ExecutionConfig(max_parallel_workers=64)


# ── Test Models ───────────────────────────────────────────

class TestModels:
    def test_test_execution_defaults(self):
        ex = TestExecution()
        assert ex.status == ExecutionStatus.QUEUED
        assert ex.attempt == 1
        assert ex.max_retries == 0
        assert ex.tags == []
        assert ex.artifacts == []
        assert ex.logs == []

    def test_test_execution_with_values(self, sample_execution):
        ex = sample_execution
        assert ex.id == "test-exec-1"
        assert ex.test_case_name == "Login Test"
        assert ex.execution_type == ExecutionType.PLAYWRIGHT
        assert ex.max_retries == 2

    def test_execution_summary_defaults(self):
        summary = ExecutionSummary()
        assert summary.total_tests == 0
        assert summary.passed == 0
        assert summary.failed == 0
        assert summary.total_duration_ms == 0.0
        assert summary.suite_results == []

    def test_step_status_enum(self):
        assert StepStatus.PASSED.value == "passed"
        assert StepStatus.FAILED.value == "failed"
        assert StepStatus.SKIPPED.value == "skipped"

    def test_execution_type_enum(self):
        assert ExecutionType.PLAYWRIGHT.value == "playwright"
        assert ExecutionType.API.value == "api"

    def test_execution_status_enum(self):
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.PASSED.value == "passed"

    def test_artifact_model(self):
        art = ExecutionArtifact(
            name="test.png",
            path="/tmp/test.png",
            type="screenshot",
            size_bytes=1024,
        )
        assert art.name == "test.png"
        assert art.type == "screenshot"

    def test_execution_log_model(self):
        log = ExecutionLog(level="ERROR", message="Something failed", source="playwright")
        assert log.level == "ERROR"
        assert log.source == "playwright"

    def test_test_step_result_with_assertions(self):
        step = TestStepResult(
            step_name="Check title",
            status=StepStatus.PASSED,
            duration_ms=100.0,
            assertion_details={"expected": "Dashboard", "actual": "Dashboard"},
        )
        assert step.assertion_details["expected"] == "Dashboard"


# ── Test LogCapture ───────────────────────────────────────

class TestLogCapture:
    def test_add_log(self):
        lc = LogCapture()
        lc.add("Test started", level="INFO", source="runner")
        assert len(lc.logs) == 1
        assert lc.logs[0].message == "Test started"
        assert lc.logs[0].level == "INFO"

    def test_raw_text(self):
        lc = LogCapture()
        lc.add("line1", level="INFO")
        lc.add("line2", level="ERROR")
        assert "[INFO] line1" in lc.raw_text
        assert "[ERROR] line2" in lc.raw_text

    def test_add_separator(self):
        lc = LogCapture()
        lc.add_separator()
        assert len(lc.logs) == 1
        assert len(lc.logs[0].message) == 60

    def test_max_bytes_respected(self):
        lc = LogCapture(max_bytes=10)
        lc.add("hello world this is too long")
        assert len(lc.logs) == 0

    def test_clear(self):
        lc = LogCapture()
        lc.add("test")
        lc.clear()
        assert len(lc.logs) == 0

    def test_merge(self):
        lc1 = LogCapture()
        lc2 = LogCapture()
        lc1.add("from1")
        lc2.add("from2")
        lc1.merge(lc2)
        assert len(lc1.logs) == 2

    @pytest.mark.asyncio
    async def test_capture_stream(self):
        lc = LogCapture()

        async def _reader():
            for line in [b"line1\n", b"line2\n"]:
                yield line

        reader = asyncio.StreamReader()
        reader.feed_data(b"line1\nline2\n")
        reader.feed_eof()

        await lc.capture_stream(reader, source="stdout", level="INFO")
        assert len(lc.logs) == 2
        assert lc.logs[0].message == "line1"


# ── Test ResultParser ─────────────────────────────────────

class TestResultParser:
    def test_parse_junit_simple(self, sample_junit_xml):
        suites = ResultParser.parse_junit_xml(sample_junit_xml)
        assert len(suites) == 2

        login_suite = suites[0]
        assert login_suite.suite_name == "LoginSuite"
        assert login_suite.total == 3
        assert login_suite.failed == 1
        assert login_suite.skipped == 1
        assert login_suite.passed == 1
        assert login_suite.duration_ms == 2500.0

        steps = login_suite.steps
        assert steps[0].status == StepStatus.PASSED
        assert steps[1].status == StepStatus.FAILED
        assert steps[1].error_message == "Expected 200, got 401"
        assert steps[2].status == StepStatus.SKIPPED

    def test_parse_junit_all_pass(self):
        xml = """<?xml version="1.0"?>
<testsuite name="AllPass" tests="2" failures="0" errors="0" time="1.0">
  <testcase name="test_a" time="0.5"/>
  <testcase name="test_b" time="0.5"/>
</testsuite>"""
        suites = ResultParser.parse_junit_xml(xml)
        assert suites[0].passed == 2
        assert suites[0].failed == 0

    def test_parse_junit_error(self):
        xml = """<?xml version="1.0"?>
<testsuite name="ErrSuite" tests="1" failures="0" errors="1" time="0.5">
  <testcase name="test_crash" time="0.5">
    <error message="Segfault">Process died</error>
  </testcase>
</testsuite>"""
        suites = ResultParser.parse_junit_xml(xml)
        assert suites[0].steps[0].status == StepStatus.ERROR
        assert suites[0].steps[0].error_message == "Segfault"

    def test_parse_json_report(self, sample_json_report, tmp_path):
        report_file = tmp_path / "report.json"
        report_file.write_text(sample_json_report)
        suites = ResultParser.parse_json_report(str(report_file))
        assert len(suites) == 1
        assert suites[0].suite_name == "API Tests"
        assert suites[0].passed == 1
        assert suites[0].failed == 1

    def test_parse_playwright_json(self, sample_playwright_json, tmp_path):
        report_file = tmp_path / "playwright-report.json"
        report_file.write_text(sample_playwright_json)
        suites = ResultParser.parse_playwright_json(str(report_file))
        assert len(suites) == 1
        assert suites[0].suite_name.startswith("login.spec.ts")
        assert suites[0].passed == 1
        assert suites[0].failed == 1

    def test_parse_nonexistent_file(self, tmp_path):
        suites = ResultParser.parse_report(tmp_path / "nope.xml", fmt="junit")
        assert suites == []

    def test_parse_report_junit(self, sample_junit_xml, tmp_path):
        f = tmp_path / "results.xml"
        f.write_text(sample_junit_xml)
        suites = ResultParser.parse_report(str(f), fmt="junit")
        assert len(suites) == 2

    def test_parse_report_unsupported_format(self, tmp_path):
        f = tmp_path / "foo.txt"
        f.write_text("dummy content")
        with pytest.raises(ValueError, match="Unsupported report format"):
            ResultParser.parse_report(str(f), fmt="unknown")

    def test_parse_playwright_empty_results(self, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("[]")
        suites = ResultParser.parse_playwright_json(str(f))
        assert suites == []

    def test_parse_json_with_empty_list(self, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("[]")
        suites = ResultParser.parse_json_report(str(f))
        assert suites == []


# ── Test ExecutionStorage ────────────────────────────────

class TestExecutionStorage:
    def test_save_and_list_screenshots(self, tmp_artifact_dir):
        storage = ExecutionStorage(tmp_artifact_dir)
        art = storage.save_screenshot("exec-1", b"fake_png_data", step_name="login")
        assert art.type == "screenshot"
        assert art.size_bytes == len(b"fake_png_data")
        assert Path(art.path).exists()

    def test_save_log(self, tmp_artifact_dir):
        storage = ExecutionStorage(tmp_artifact_dir)
        art = storage.save_log("exec-1", "line1\nline2\n")
        assert art.type == "log"
        assert Path(art.path).exists()
        assert Path(art.path).read_text() == "line1\nline2\n"

    def test_save_report(self, tmp_artifact_dir):
        storage = ExecutionStorage(tmp_artifact_dir)
        art = storage.save_report("exec-1", "<xml/>", filename="test.xml")
        assert art.type == "report"
        assert art.name == "test.xml"

    def test_save_execution_result(self, tmp_artifact_dir, sample_execution):
        storage = ExecutionStorage(tmp_artifact_dir)
        art = storage.save_execution_result("exec-1", sample_execution)
        assert Path(art.path).exists()
        data = json.loads(Path(art.path).read_text())
        assert data["id"] == "test-exec-1"

    def test_save_artifact_bytes(self, tmp_artifact_dir):
        storage = ExecutionStorage(tmp_artifact_dir)
        art = storage.save_artifact("exec-1", b"binary", "data.bin", artifact_type="other")
        assert art.size_bytes == 6

    def test_save_artifact_string(self, tmp_artifact_dir):
        storage = ExecutionStorage(tmp_artifact_dir)
        art = storage.save_artifact("exec-1", "text", "data.txt", artifact_type="other")
        assert art.size_bytes == 4

    def test_list_artifacts(self, tmp_artifact_dir):
        storage = ExecutionStorage(tmp_artifact_dir)
        storage.save_log("exec-1", "log content")
        storage.save_screenshot("exec-1", b"img")
        artifacts = storage.list_artifacts("exec-1")
        assert len(artifacts) == 2

    def test_list_nonexistent(self, tmp_artifact_dir):
        storage = ExecutionStorage(tmp_artifact_dir)
        assert storage.list_artifacts("no-such-exec") == []

    def test_cleanup(self, tmp_artifact_dir):
        storage = ExecutionStorage(tmp_artifact_dir)
        storage.save_log("exec-1", "content")
        assert Path(tmp_artifact_dir, "exec-1").exists()
        storage.cleanup("exec-1")
        assert not Path(tmp_artifact_dir, "exec-1").exists()

    def test_infer_type(self):
        storage = ExecutionStorage("/tmp")
        assert storage._infer_type(".png") == "screenshot"
        assert storage._infer_type(".log") == "log"
        assert storage._infer_type(".xml") == "report"
        assert storage._infer_type(".mp4") == "video"
        assert storage._infer_type(".zip") == "trace"
        assert storage._infer_type(".unknown") == "other"


# ── Test SummaryGenerator ─────────────────────────────────

class TestSummaryGenerator:
    def test_from_suite_results(self):
        suites = [
            TestSuiteResult(
                suite_name="Suite1",
                total=3,
                passed=2,
                failed=1,
                skipped=0,
                error=0,
                duration_ms=1500.0,
            )
        ]
        summary = SummaryGenerator.from_suite_results(suites)
        assert summary.total_tests == 3
        assert summary.passed == 2
        assert summary.failed == 1
        assert summary.total_duration_ms == 1500.0
        assert len(summary.suite_results) == 1

    def test_from_steps(self):
        steps = [
            TestStepResult(step_name="s1", status=StepStatus.PASSED, duration_ms=100),
            TestStepResult(step_name="s2", status=StepStatus.FAILED, duration_ms=50),
            TestStepResult(step_name="s3", status=StepStatus.SKIPPED),
        ]
        summary = SummaryGenerator.from_steps(steps)
        assert summary.total_tests == 3
        assert summary.passed == 1
        assert summary.failed == 1
        assert summary.skipped == 1

    def test_from_execution(self, sample_execution):
        sample_execution.started_at = datetime(2024, 1, 1, 10, 0, 0)
        sample_execution.completed_at = datetime(2024, 1, 1, 10, 1, 0)
        sample_execution.duration_ms = 60000.0
        summary = SummaryGenerator.from_execution(sample_execution)
        assert summary.start_time == sample_execution.started_at
        assert summary.end_time == sample_execution.completed_at
        assert summary.total_duration_ms == 60000.0

    def test_format_summary_text(self):
        summary = ExecutionSummary(
            total_tests=10,
            passed=8,
            failed=2,
            skipped=0,
            error=0,
            total_duration_ms=5000.0,
        )
        text = SummaryGenerator.format_summary_text(summary)
        assert "Passed:         8" in text
        assert "Failed:         2" in text
        assert "5000 ms" in text

    def test_pass_rate(self):
        s1 = ExecutionSummary(total_tests=10, passed=5)
        assert SummaryGenerator.pass_rate(s1) == 50.0

        s2 = ExecutionSummary(total_tests=0)
        assert SummaryGenerator.pass_rate(s2) == 100.0

    def test_is_successful(self):
        assert SummaryGenerator.is_successful(ExecutionSummary(total_tests=5, passed=5)) is True
        assert SummaryGenerator.is_successful(ExecutionSummary(total_tests=5, passed=4, failed=1)) is False


# ── Test PlaywrightRunner (mocked) ────────────────────────

class TestPlaywrightRunner:
    @pytest.mark.asyncio
    async def test_run_success(self, tmp_artifact_dir, sample_execution):
        config = ExecutionConfig(artifact_dir=tmp_artifact_dir)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            process_mock = AsyncMock()
            process_mock.stdout = asyncio.StreamReader()
            process_mock.stderr = asyncio.StreamReader()
            process_mock.stdout.feed_eof()
            process_mock.stderr.feed_eof()
            process_mock.wait = AsyncMock(return_value=0)
            mock_create.return_value = process_mock

            from app.execution.playwright_runner import PlaywrightRunner

            runner = PlaywrightRunner(config)
            result = await runner.run(sample_execution)

            assert result.status == ExecutionStatus.PASSED
            assert result.duration_ms is not None
            assert len(result.logs) > 0

    @pytest.mark.asyncio
    async def test_run_timeout(self, tmp_artifact_dir, sample_execution):
        config = ExecutionConfig(artifact_dir=tmp_artifact_dir, timeout_seconds=1)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            process_mock = AsyncMock()
            process_mock.stdout = asyncio.StreamReader()
            process_mock.stderr = asyncio.StreamReader()
            process_mock.stdout.feed_eof()
            process_mock.stderr.feed_eof()

            async def slow_wait():
                await asyncio.sleep(10)
                return 1

            process_mock.wait = slow_wait
            process_mock.kill = MagicMock()
            mock_create.return_value = process_mock

            from app.execution.playwright_runner import PlaywrightRunner

            runner = PlaywrightRunner(config)
            result = await runner.run(sample_execution)

            assert result.status == ExecutionStatus.TIMEOUT
            assert "Timed out" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_run_file_not_found(self, tmp_artifact_dir, sample_execution):
        config = ExecutionConfig(artifact_dir=tmp_artifact_dir, playwright_binary="nonexistent-cmd")

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            from app.execution.playwright_runner import PlaywrightRunner

            runner = PlaywrightRunner(config)
            result = await runner.run(sample_execution)

            assert result.status == ExecutionStatus.ERROR
            assert "not found" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_run_generic_exception(self, tmp_artifact_dir, sample_execution):
        config = ExecutionConfig(artifact_dir=tmp_artifact_dir)

        with patch("asyncio.create_subprocess_exec", side_effect=RuntimeError("unexpected crash")):
            from app.execution.playwright_runner import PlaywrightRunner

            runner = PlaywrightRunner(config)
            result = await runner.run(sample_execution)

            assert result.status == ExecutionStatus.ERROR
            assert "unexpected crash" in (result.error_message or "")


# ── Test ApiTestRunner (mocked) ───────────────────────────

class TestApiTestRunner:
    @pytest.mark.asyncio
    async def test_run_success(self, tmp_artifact_dir):
        config = ExecutionConfig(artifact_dir=tmp_artifact_dir)
        execution = TestExecution(
            id="api-test-1",
            test_case_id="tc-api",
            test_case_name="API Health Check",
            execution_type=ExecutionType.API,
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            process_mock = AsyncMock()
            process_mock.stdout = asyncio.StreamReader()
            process_mock.stderr = asyncio.StreamReader()
            process_mock.stdout.feed_eof()
            process_mock.stderr.feed_eof()
            process_mock.wait = AsyncMock(return_value=0)
            mock_create.return_value = process_mock

            from app.execution.api_runner import ApiTestRunner

            runner = ApiTestRunner(config)
            result = await runner.run(execution)

            assert result.status in (ExecutionStatus.PASSED, ExecutionStatus.RUNNING)
            assert result.duration_ms is not None


# ── Test TestExecutionEngine ──────────────────────────────

class TestTestExecutionEngine:
    @pytest.mark.asyncio
    async def test_engine_execute_playwright(self, tmp_artifact_dir, sample_execution):
        config = ExecutionConfig(artifact_dir=tmp_artifact_dir)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            process_mock = AsyncMock()
            process_mock.stdout = asyncio.StreamReader()
            process_mock.stderr = asyncio.StreamReader()
            process_mock.stdout.feed_eof()
            process_mock.stderr.feed_eof()
            process_mock.wait = AsyncMock(return_value=0)
            mock_create.return_value = process_mock

            from app.execution.runner import TestExecutionEngine

            engine = TestExecutionEngine(config)
            result = await engine.execute(sample_execution)

            assert result.status == ExecutionStatus.PASSED

    @pytest.mark.asyncio
    async def test_engine_retry_then_pass(self, tmp_artifact_dir):
        config = ExecutionConfig(artifact_dir=tmp_artifact_dir, max_retries=2, retry_delay_seconds=0.01)

        execution = TestExecution(
            id="retry-test",
            test_case_id="tc-retry",
            test_case_name="Retry Test",
            execution_type=ExecutionType.PLAYWRIGHT,
            max_retries=2,
        )

        call_count = 0

        original_run = None

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            process_mock = AsyncMock()
            process_mock.stdout = asyncio.StreamReader()
            process_mock.stderr = asyncio.StreamReader()
            process_mock.stdout.feed_eof()
            process_mock.stderr.feed_eof()

            async def mock_wait():
                nonlocal call_count
                call_count += 1
                return 0 if call_count >= 2 else 1

            process_mock.wait = mock_wait
            mock_create.return_value = process_mock

            from app.execution.runner import TestExecutionEngine

            engine = TestExecutionEngine(config)
            result = await engine.execute(execution)

            assert result.status == ExecutionStatus.PASSED
            assert result.summary.retries_used == 1

    @pytest.mark.asyncio
    async def test_engine_retry_exhausted(self, tmp_artifact_dir):
        config = ExecutionConfig(artifact_dir=tmp_artifact_dir, max_retries=1, retry_delay_seconds=0.01)

        execution = TestExecution(
            id="retry-exhaust",
            test_case_id="tc-exhaust",
            test_case_name="Exhaust Retries",
            execution_type=ExecutionType.PLAYWRIGHT,
            max_retries=1,
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            process_mock = AsyncMock()
            process_mock.stdout = asyncio.StreamReader()
            process_mock.stderr = asyncio.StreamReader()
            process_mock.stdout.feed_eof()
            process_mock.stderr.feed_eof()
            process_mock.wait = AsyncMock(return_value=1)
            mock_create.return_value = process_mock

            from app.execution.runner import TestExecutionEngine

            engine = TestExecutionEngine(config)
            result = await engine.execute(execution)

            assert result.status == ExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_engine_batch(self, tmp_artifact_dir):
        config = ExecutionConfig(artifact_dir=tmp_artifact_dir, max_parallel_workers=4)

        executions = [
            TestExecution(
                id=f"batch-{i}",
                test_case_id=f"tc-{i}",
                test_case_name=f"Test {i}",
                execution_type=ExecutionType.PLAYWRIGHT,
            )
            for i in range(3)
        ]

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            process_mock = AsyncMock()
            process_mock.stdout = asyncio.StreamReader()
            process_mock.stderr = asyncio.StreamReader()
            process_mock.stdout.feed_eof()
            process_mock.stderr.feed_eof()
            process_mock.wait = AsyncMock(return_value=0)
            mock_create.return_value = process_mock

            from app.execution.runner import TestExecutionEngine

            engine = TestExecutionEngine(config)
            results = await engine.execute_batch(executions)

            assert len(results) == 3
            for r in results:
                assert r.status == ExecutionStatus.PASSED

    @pytest.mark.asyncio
    async def test_engine_execute_with_timeout(self, tmp_artifact_dir, sample_execution):
        config = ExecutionConfig(artifact_dir=tmp_artifact_dir, timeout_seconds=1)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            process_mock = AsyncMock()
            process_mock.stdout = asyncio.StreamReader()
            process_mock.stderr = asyncio.StreamReader()
            process_mock.stdout.feed_eof()
            process_mock.stderr.feed_eof()

            async def slow_wait():
                await asyncio.sleep(10)
                return 0

            process_mock.wait = slow_wait
            process_mock.kill = MagicMock()
            mock_create.return_value = process_mock

            from app.execution.runner import TestExecutionEngine

            engine = TestExecutionEngine(config)
            result = await engine.execute_with_timeout(sample_execution, timeout_seconds=1)

            assert result.status == ExecutionStatus.TIMEOUT

    def test_backoff_delay(self):
        from app.execution.runner import TestExecutionEngine

        assert TestExecutionEngine._backoff_delay(1) == 2.0
        assert TestExecutionEngine._backoff_delay(2) == 4.0
        assert TestExecutionEngine._backoff_delay(3) == 8.0
        assert TestExecutionEngine._backoff_delay(10) == 60.0  # capped at 60s

    def test_create_execution(self):
        from app.execution.runner import TestExecutionEngine

        ex = TestExecutionEngine.create_execution(
            test_case_id="tc-1",
            test_case_name="My Test",
            execution_type=ExecutionType.API,
            script='def test_foo(): pass',
            parameters={"env": "staging"},
            tags=["smoke"],
            max_retries=2,
        )
        assert ex.test_case_id == "tc-1"
        assert ex.test_case_name == "My Test"
        assert ex.execution_type == ExecutionType.API
        assert ex.max_retries == 2


# ── Test API Endpoints (via TestClient) ───────────────────

class TestExecutionAPI:
    @pytest.mark.asyncio
    async def test_execute_endpoint(self, tmp_artifact_dir, client, sample_execution):
        config = ExecutionConfig(artifact_dir=tmp_artifact_dir)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            process_mock = AsyncMock()
            process_mock.stdout = asyncio.StreamReader()
            process_mock.stderr = asyncio.StreamReader()
            process_mock.stdout.feed_eof()
            process_mock.stderr.feed_eof()
            process_mock.wait = AsyncMock(return_value=0)
            mock_create.return_value = process_mock

            response = client.post(
                "/api/v1/execution/execute",
                json={
                    "test_case_id": "tc-1",
                    "test_case_name": "Login Test",
                    "execution_type": "playwright",
                    "script": 'test("login", async () => {});',
                    "max_retries": 1,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ("passed", "running")

    @pytest.mark.asyncio
    async def test_batch_execute_endpoint(self, tmp_artifact_dir, client):
        config = ExecutionConfig(artifact_dir=tmp_artifact_dir)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            process_mock = AsyncMock()
            process_mock.stdout = asyncio.StreamReader()
            process_mock.stderr = asyncio.StreamReader()
            process_mock.stdout.feed_eof()
            process_mock.stderr.feed_eof()
            process_mock.wait = AsyncMock(return_value=0)
            mock_create.return_value = process_mock

            response = client.post(
                "/api/v1/execution/execute/batch",
                json={
                    "tests": [
                        {
                            "test_case_id": "tc-1",
                            "test_case_name": "Test 1",
                            "execution_type": "playwright",
                        },
                        {
                            "test_case_id": "tc-2",
                            "test_case_name": "Test 2",
                            "execution_type": "playwright",
                        },
                    ],
                    "max_parallel": 2,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    def test_get_config_endpoint(self, client):
        response = client.get("/api/v1/execution/config")
        assert response.status_code == 200
        data = response.json()
        assert data["max_retries"] == 3

    def test_update_config_endpoint(self, client):
        response = client.put(
            "/api/v1/execution/config",
            json={
                "max_retries": 5,
                "retry_delay_seconds": 3.0,
                "timeout_seconds": 600,
                "max_parallel_workers": 8,
                "artifact_dir": ".execution_artifacts",
                "playwright_binary": "npx playwright",
                "pytest_args": ["-v", "--tb=short"],
                "report_format": "junit",
                "screenshot_on_failure": True,
                "capture_stdout": True,
                "capture_stderr": True,
                "log_max_bytes": 10485760,
                "jupiter_timeout_seconds": 60,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["max_retries"] == 5

    def test_execute_by_type_playwright(self, tmp_artifact_dir, client):
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create:
            process_mock = AsyncMock()
            process_mock.stdout = asyncio.StreamReader()
            process_mock.stderr = asyncio.StreamReader()
            process_mock.stdout.feed_eof()
            process_mock.stderr.feed_eof()
            process_mock.wait = AsyncMock(return_value=0)
            mock_create.return_value = process_mock

            response = client.post(
                "/api/v1/execution/execute/playwright?test_file=tests/foo.spec.ts&test_case_id=tc-1",
            )
            assert response.status_code == 200

    def test_execute_by_type_invalid(self, client):
        response = client.post(
            "/api/v1/execution/execute/invalid?test_file=tests/foo.spec.ts",
        )
        assert response.status_code == 400


# ── Conftest for TestClient ───────────────────────────────

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)
