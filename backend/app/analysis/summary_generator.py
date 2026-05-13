from app.analysis.models import (
    AnalysisSummary,
    RiskLevel,
    RootCauseSuggestion,
    FailureCategoryResult,
    RetryRecommendation,
    RiskAssessment,
    AnalysisInput,
)


class SummaryGenerator:
    @staticmethod
    def generate(
        input_data: AnalysisInput,
        root_cause: RootCauseSuggestion,
        category_result: FailureCategoryResult,
        risk: RiskAssessment,
        retry: RetryRecommendation,
    ) -> AnalysisSummary:
        one_liner = SummaryGenerator._build_one_liner(
            input_data, category_result, root_cause
        )
        detailed = SummaryGenerator._build_detailed(
            input_data, root_cause, category_result, risk
        )
        findings = SummaryGenerator._build_findings(
            root_cause, category_result, risk
        )
        actions = SummaryGenerator._build_actions(
            root_cause, retry, risk
        )

        return AnalysisSummary(
            one_liner=one_liner,
            detailed_summary=detailed,
            key_findings=findings,
            recommended_actions=actions,
            severity=risk.level,
        )

    @staticmethod
    def _build_one_liner(
        input_data: AnalysisInput,
        category_result: FailureCategoryResult,
        root_cause: RootCauseSuggestion,
    ) -> str:
        test = input_data.test_name or "Unknown test"
        cat = category_result.primary_category.value
        cause = root_cause.title or "unknown cause"
        return f"[{cat.upper()}] {test} failed due to {cause}"

    @staticmethod
    def _build_detailed(
        input_data: AnalysisInput,
        root_cause: RootCauseSuggestion,
        category_result: FailureCategoryResult,
        risk: RiskAssessment,
    ) -> str:
        parts = [
            f"Test '{input_data.test_name}' in suite '{input_data.test_suite}' "
            f"failed with category '{category_result.primary_category.value}'.",
        ]

        if root_cause.description:
            parts.append(f"Root cause: {root_cause.description}")

        if root_cause.suggested_fix:
            parts.append(f"Suggested fix: {root_cause.suggested_fix}")

        parts.append(f"Risk level: {risk.level.value} (score: {risk.score})")

        if input_data.duration_ms:
            parts.append(f"Duration: {input_data.duration_ms:.0f} ms")

        return " ".join(parts)

    @staticmethod
    def _build_findings(
        root_cause: RootCauseSuggestion,
        category_result: FailureCategoryResult,
        risk: RiskAssessment,
    ) -> list[str]:
        findings = []

        if root_cause.evidence:
            findings.append(f"Evidence: {'; '.join(root_cause.evidence[:3])}")

        if root_cause.confidence > 0:
            findings.append(
                f"Root cause confidence: {root_cause.confidence:.0%}"
            )

        findings.append(
            f"Classification: {category_result.primary_category.value} "
            f"(confidence: {category_result.confidence:.0%})"
        )

        findings.append(f"Risk: {risk.level.value} ({risk.score:.0%})")

        if risk.impacted_areas:
            findings.append(
                f"Impacted: {', '.join(risk.impacted_areas[:3])}"
            )

        return findings

    @staticmethod
    def _build_actions(
        root_cause: RootCauseSuggestion,
        retry: RetryRecommendation,
        risk: RiskAssessment,
    ) -> list[str]:
        actions = []

        if retry.should_retry:
            actions.append(
                f"Retry recommended (max {retry.suggested_max_retries}x, "
                f"delay {retry.suggested_delay_seconds}s)"
            )
        else:
            actions.append("Do not retry — fix the root cause first")

        if root_cause.suggested_fix:
            actions.append(f"Apply fix: {root_cause.suggested_fix}")

        if risk.level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            actions.append("Escalate — high/critical risk failure")

        return actions
