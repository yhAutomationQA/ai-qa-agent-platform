from app.analysis.models import (
    RiskAssessment,
    RiskLevel,
    FailureCategory,
    AnalysisInput,
    FailureCategoryResult,
)


class RiskAnalyzer:
    CATEGORY_RISK_MAP: dict[FailureCategory, RiskLevel] = {
        FailureCategory.PERMISSION: RiskLevel.CRITICAL,
        FailureCategory.INFRASTRUCTURE: RiskLevel.CRITICAL,
        FailureCategory.DEPENDENCY: RiskLevel.HIGH,
        FailureCategory.API: RiskLevel.HIGH,
        FailureCategory.DATA: RiskLevel.HIGH,
        FailureCategory.ASSERTION: RiskLevel.MEDIUM,
        FailureCategory.STATE: RiskLevel.MEDIUM,
        FailureCategory.TIMEOUT: RiskLevel.MEDIUM,
        FailureCategory.UI: RiskLevel.LOW,
        FailureCategory.NETWORK: RiskLevel.LOW,
        FailureCategory.ENVIRONMENT: RiskLevel.LOW,
        FailureCategory.FLAKY: RiskLevel.LOW,
        FailureCategory.UNKNOWN: RiskLevel.MEDIUM,
    }

    CATEGORY_BLAST_RADIUS: dict[FailureCategory, str] = {
        FailureCategory.PERMISSION: "All users and operations in the affected security context",
        FailureCategory.INFRASTRUCTURE: "Entire test suite or deployment pipeline",
        FailureCategory.DEPENDENCY: "All tests and features relying on the external service",
        FailureCategory.API: "All consumers of the affected API endpoint",
        FailureCategory.DATA: "Tests and features using the affected data set",
        FailureCategory.ASSERTION: "Isolated to the specific test case",
        FailureCategory.STATE: "Subsequent tests in the same run",
        FailureCategory.TIMEOUT: "Potentially indicates deeper performance or availability issue",
        FailureCategory.UI: "Isolated to the specific UI component",
        FailureCategory.NETWORK: "May affect all tests in the network scope",
        FailureCategory.ENVIRONMENT: "All tests in the affected environment",
        FailureCategory.FLAKY: "Intermittent, low blast radius",
        FailureCategory.UNKNOWN: "Cannot determine blast radius",
    }

    CATEGORY_IMPACTED_AREAS: dict[FailureCategory, list[str]] = {
        FailureCategory.PERMISSION: ["Authentication", "Authorization", "Security"],
        FailureCategory.INFRASTRUCTURE: ["CI/CD", "Deployment", "Infrastructure"],
        FailureCategory.DEPENDENCY: ["External integrations", "Third-party services"],
        FailureCategory.API: ["API contracts", "Backend services", "Integration"],
        FailureCategory.DATA: ["Test data", "Database", "Data integrity"],
        FailureCategory.ASSERTION: ["Functional correctness"],
        FailureCategory.STATE: ["Test isolation", "Shared state"],
        FailureCategory.TIMEOUT: ["Performance", "Reliability"],
        FailureCategory.UI: ["UI/UX", "Frontend"],
        FailureCategory.NETWORK: ["Network", "Connectivity"],
        FailureCategory.ENVIRONMENT: ["Environment configuration"],
        FailureCategory.FLAKY: ["Test stability"],
        FailureCategory.UNKNOWN: ["Unknown"],
    }

    def analyze(
        self,
        input_data: AnalysisInput,
        category_result: FailureCategoryResult,
    ) -> RiskAssessment:
        base_level = self.CATEGORY_RISK_MAP.get(
            category_result.primary_category, RiskLevel.MEDIUM
        )
        base_score = self._level_to_score(base_level)
        modifiers = self._calculate_modifiers(input_data)
        final_score = max(0.0, min(1.0, base_score + modifiers))

        level = self._score_to_level(final_score)

        return RiskAssessment(
            level=level,
            score=round(final_score, 2),
            impacted_areas=self.CATEGORY_IMPACTED_AREAS.get(
                category_result.primary_category, ["Unknown"]
            ),
            blast_radius=self.CATEGORY_BLAST_RADIUS.get(
                category_result.primary_category, "Unknown"
            ),
            reasoning=self._build_reasoning(
                category_result, base_level, modifiers, level
            ),
        )

    def _calculate_modifiers(self, input_data: AnalysisInput) -> float:
        modifiers = 0.0

        if input_data.retry_count > 2:
            modifiers += 0.1

        if input_data.api_status_code and input_data.api_status_code >= 500:
            modifiers += 0.15

        if input_data.error_message:
            error_lower = input_data.error_message.lower()
            if "security" in error_lower or "auth" in error_lower or "permission" in error_lower:
                modifiers += 0.2
            if "crash" in error_lower or "segfault" in error_lower or "null" in error_lower:
                modifiers += 0.15

        if input_data.duration_ms and input_data.duration_ms > 60_000:
            modifiers += 0.05

        if input_data.tags:
            if "critical" in input_data.tags or "p0" in input_data.tags or "blocker" in input_data.tags:
                modifiers += 0.2
            if "regression" in input_data.tags:
                modifiers += 0.15

        return modifiers

    def _build_reasoning(
        self,
        category_result: FailureCategoryResult,
        base_level: RiskLevel,
        modifiers: float,
        final_level: RiskLevel,
    ) -> str:
        parts = [
            f"Primary category: {category_result.primary_category.value}",
            f"Base risk: {base_level.value}",
        ]
        if modifiers > 0:
            parts.append(f"Risk modifiers applied: +{modifiers:.2f}")
        parts.append(f"Final risk level: {final_level.value}")
        return ". ".join(parts)

    @staticmethod
    def _level_to_score(level: RiskLevel) -> float:
        mapping = {
            RiskLevel.CRITICAL: 0.9,
            RiskLevel.HIGH: 0.7,
            RiskLevel.MEDIUM: 0.4,
            RiskLevel.LOW: 0.15,
        }
        return mapping.get(level, 0.4)

    @staticmethod
    def _score_to_level(score: float) -> RiskLevel:
        if score >= 0.8:
            return RiskLevel.CRITICAL
        if score >= 0.6:
            return RiskLevel.HIGH
        if score >= 0.3:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @staticmethod
    def aggregate_risk(assessments: list[RiskAssessment]) -> RiskAssessment:
        if not assessments:
            return RiskAssessment()

        max_score = max(a.score for a in assessments)
        all_areas: list[str] = []
        for a in assessments:
            all_areas.extend(a.impacted_areas)
        unique_areas = list(dict.fromkeys(all_areas))

        max_assessment = max(assessments, key=lambda a: a.score)

        return RiskAssessment(
            level=max_assessment.level,
            score=round(max_score, 2),
            impacted_areas=unique_areas,
            blast_radius=f"Highest risk from: {max_assessment.blast_radius}",
            reasoning=f"Aggregate of {len(assessments)} assessments. "
            f"Max risk score: {max_score:.2f} ({max_assessment.level.value})",
        )
