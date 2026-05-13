import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from app.execution.models import TestSuiteResult, TestStepResult, StepStatus


class ResultParser:
    @staticmethod
    def parse_junit_xml(xml_content: str) -> list[TestSuiteResult]:
        root = ET.fromstring(xml_content)
        suites: list[TestSuiteResult] = []

        for suite_elem in root.iter("testsuite"):
            suite_name = suite_elem.get("name", "unnamed")
            suite = TestSuiteResult(
                suite_name=suite_name,
                total=int(suite_elem.get("tests", 0)),
                failed=int(suite_elem.get("failures", 0)),
                error=int(suite_elem.get("errors", 0)),
                skipped=int(suite_elem.get("skipped", 0)),
                duration_ms=float(suite_elem.get("time", 0)) * 1000,
            )
            suite.passed = suite.total - suite.failed - suite.error - suite.skipped

            for case_elem in suite_elem.iter("testcase"):
                class_name = case_elem.get("classname", "")
                test_name = case_elem.get("name", "unnamed")
                step_name = f"{class_name}.{test_name}" if class_name else test_name
                time_sec = float(case_elem.get("time", 0))

                failure = case_elem.find("failure")
                error_elem = case_elem.find("error")
                skipped_elem = case_elem.find("skipped")

                if failure is not None:
                    status = StepStatus.FAILED
                    error_msg = failure.get("message", failure.text or "")
                elif error_elem is not None:
                    status = StepStatus.ERROR
                    error_msg = error_elem.get("message", error_elem.text or "")
                elif skipped_elem is not None:
                    status = StepStatus.SKIPPED
                    error_msg = None
                else:
                    status = StepStatus.PASSED
                    error_msg = None

                suite.steps.append(
                    TestStepResult(
                        step_name=step_name,
                        status=status,
                        duration_ms=time_sec * 1000,
                        error_message=error_msg,
                    )
                )

            suites.append(suite)

        return suites

    @staticmethod
    def parse_json_report(report_path: str | Path) -> list[TestSuiteResult]:
        path = Path(report_path)
        if not path.exists():
            return []

        with open(path) as f:
            data = json.load(f)

        suites: list[TestSuiteResult] = []

        if isinstance(data, list):
            suites_data = data
        elif isinstance(data, dict):
            suites_data = data.get("suites", data.get("results", [data]))

        for suite_entry in suites_data:
            suite_name = suite_entry.get("name", suite_entry.get("title", "unnamed"))
            suite = TestSuiteResult(suite_name=suite_name)

            cases = suite_entry.get("tests", suite_entry.get("cases", suite_entry.get("specs", [])))
            for case in cases:
                title = case.get("title", case.get("name", "unnamed"))
                status_raw = case.get("status", "unknown").lower()
                duration = case.get("duration_ms", case.get("duration", 0))
                error = case.get("error", case.get("failure", case.get("err_message")))

                if status_raw in ("passed", "success"):
                    status = StepStatus.PASSED
                elif status_raw in ("failed", "failure"):
                    status = StepStatus.FAILED
                elif status_raw in ("skipped", "pending"):
                    status = StepStatus.SKIPPED
                else:
                    status = StepStatus.ERROR

                suite.steps.append(
                    TestStepResult(
                        step_name=title,
                        status=status,
                        duration_ms=float(duration) if duration else None,
                        error_message=str(error) if error else None,
                    )
                )

            suite.total = len(suite.steps)
            suite.passed = sum(1 for s in suite.steps if s.status == StepStatus.PASSED)
            suite.failed = sum(1 for s in suite.steps if s.status == StepStatus.FAILED)
            suite.skipped = sum(1 for s in suite.steps if s.status == StepStatus.SKIPPED)
            suite.error = sum(1 for s in suite.steps if s.status == StepStatus.ERROR)

            if suite.steps:
                suite.duration_ms = sum(
                    s.duration_ms or 0 for s in suite.steps
                )

            suites.append(suite)

        return suites

    @staticmethod
    def parse_playwright_json(report_path: str | Path) -> list[TestSuiteResult]:
        path = Path(report_path)
        if not path.exists():
            return []

        with open(path) as f:
            data = json.load(f)

        suites: list[TestSuiteResult] = []

        if isinstance(data, dict):
            data = [data]

        for suite_entry in data:
            suite_name = suite_entry.get("file", suite_entry.get("title", "unnamed"))
            suite = TestSuiteResult(suite_name=suite_name)

            specs = suite_entry.get("specs", [])
            for spec in specs:
                spec_title = spec.get("title", "unnamed")
                tests = spec.get("tests", [])
                for test in tests:
                    results = test.get("results", [])
                    for result in results:
                        step_name = spec_title
                        status_raw = result.get("status", "unknown").lower()
                        duration = result.get("duration", 0)
                        error = result.get("error", None)

                        if status_raw == "expected":
                            status = StepStatus.PASSED
                        elif status_raw == "unexpected":
                            status = StepStatus.FAILED
                        elif status_raw == "skipped":
                            status = StepStatus.SKIPPED
                        else:
                            status = StepStatus.ERROR

                        suite.steps.append(
                            TestStepResult(
                                step_name=step_name,
                                status=status,
                                duration_ms=float(duration) / 1000 if duration else None,
                                error_message=str(error) if error else None,
                            )
                        )

            suite.total = len(suite.steps)
            suite.passed = sum(1 for s in suite.steps if s.status == StepStatus.PASSED)
            suite.failed = sum(1 for s in suite.steps if s.status == StepStatus.FAILED)
            suite.skipped = sum(1 for s in suite.steps if s.status == StepStatus.SKIPPED)
            suite.error = sum(1 for s in suite.steps if s.status == StepStatus.ERROR)

            if suite.steps:
                total_ms = sum(s.duration_ms or 0 for s in suite.steps)
                suite.duration_ms = total_ms

            suites.append(suite)

        return suites

    @classmethod
    def parse_report(cls, report_path: str | Path, fmt: str = "junit") -> list[TestSuiteResult]:
        path = Path(report_path)
        if not path.exists():
            return []

        raw = path.read_text(encoding="utf-8")

        if fmt == "junit":
            return cls.parse_junit_xml(raw)
        elif fmt == "json":
            return cls.parse_json_report(report_path)
        elif fmt == "playwright":
            return cls.parse_playwright_json(report_path)
        else:
            raise ValueError(f"Unsupported report format: {fmt}")
