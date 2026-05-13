from datetime import datetime

from app.execution.models import (
    TestExecution,
    TestSuiteResult,
    TestStepResult,
    ExecutionSummary,
)


class SummaryGenerator:
    @staticmethod
    def from_execution(execution: TestExecution) -> ExecutionSummary:
        summary = execution.summary
        summary.start_time = execution.started_at
        summary.end_time = execution.completed_at
        summary.total_duration_ms = execution.duration_ms or 0.0
        return summary

    @staticmethod
    def from_suite_results(suite_results: list[TestSuiteResult]) -> ExecutionSummary:
        summary = ExecutionSummary()

        for suite in suite_results:
            summary.total_tests += suite.total
            summary.passed += suite.passed
            summary.failed += suite.failed
            summary.skipped += suite.skipped
            summary.error += suite.error
            summary.total_duration_ms += suite.duration_ms or 0.0
            summary.suite_results.append(suite)

        return summary

    @staticmethod
    def from_steps(steps: list[TestStepResult]) -> ExecutionSummary:
        suite = TestSuiteResult(suite_name="default", steps=steps)
        suite.total = len(steps)
        suite.passed = sum(1 for s in steps if s.status.value == "passed")
        suite.failed = sum(1 for s in steps if s.status.value == "failed")
        suite.skipped = sum(1 for s in steps if s.status.value == "skipped")
        suite.error = sum(1 for s in steps if s.status.value == "error")
        suite.duration_ms = sum(s.duration_ms or 0 for s in steps)

        return SummaryGenerator.from_suite_results([suite])

    @staticmethod
    def format_summary_text(summary: ExecutionSummary) -> str:
        lines = [
            "=" * 50,
            "EXECUTION SUMMARY",
            "=" * 50,
            f"Total Tests:    {summary.total_tests}",
            f"Passed:         {summary.passed}",
            f"Failed:         {summary.failed}",
            f"Skipped:        {summary.skipped}",
            f"Errors:         {summary.error}",
            f"Total Duration: {summary.total_duration_ms:.0f} ms",
            f"Retries Used:   {summary.retries_used} / {summary.max_retries}",
            "-" * 50,
        ]

        if summary.start_time:
            lines.append(f"Started:  {summary.start_time.isoformat()}")
        if summary.end_time:
            lines.append(f"Ended:    {summary.end_time.isoformat()}")

        if summary.suite_results:
            lines.append("")
            lines.append("SUITE RESULTS:")
            for suite in summary.suite_results:
                status = "PASS" if suite.failed == 0 and suite.error == 0 else "FAIL"
                lines.append(
                    f"  [{status}] {suite.suite_name}: "
                    f"{suite.passed}/{suite.total} passed "
                    f"({suite.duration_ms:.0f} ms)"
                )

        lines.append("=" * 50)
        return "\n".join(lines)

    @staticmethod
    def pass_rate(summary: ExecutionSummary) -> float:
        if summary.total_tests == 0:
            return 100.0
        return round((summary.passed / summary.total_tests) * 100, 2)

    @staticmethod
    def is_successful(summary: ExecutionSummary) -> bool:
        return summary.failed == 0 and summary.error == 0
