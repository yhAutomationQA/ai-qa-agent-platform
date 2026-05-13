import structlog
from typing import Any

from app.analysis.config import analysis_settings
from app.analysis.models import (
    AnalysisInput,
    BatchAnalysisInput,
    FailureAnalysis,
    BatchAnalysisResult,
)
from app.analysis.result_analyzer import ResultAnalyzer

logger = structlog.get_logger()


class AnalysisService:
    def __init__(self, ai_client=None):
        self._analyzer = ResultAnalyzer(ai_client)
        self._ai_client = ai_client

    async def analyze_failure(
        self,
        input_data: AnalysisInput,
        use_ai: bool | None = None,
    ) -> FailureAnalysis:
        logger.info(
            "analysis_requested",
            test_name=input_data.test_name,
            execution_type=input_data.execution_type,
            use_ai=use_ai,
        )

        result = await self._analyzer.analyze(input_data, use_ai=use_ai)

        logger.info(
            "analysis_completed",
            analysis_id=result.analysis_id,
            category=result.category.primary_category.value,
            risk=result.risk.level.value,
            ai_used=result.ai_used,
            duration_ms=result.duration_ms,
        )

        return result

    async def analyze_batch(
        self,
        batch: BatchAnalysisInput,
        use_ai: bool | None = None,
    ) -> BatchAnalysisResult:
        logger.info(
            "batch_analysis_requested",
            failure_count=len(batch.failures),
            use_ai=use_ai,
        )

        result = await self._analyzer.analyze_batch(batch, use_ai=use_ai)

        logger.info(
            "batch_analysis_completed",
            total_analyzed=result.total_analyzed,
            overall_risk=result.overall_risk.value,
            duration_ms=result.analysis_duration_ms,
        )

        return result

    async def analyze_from_execution(
        self,
        execution: Any,
        use_ai: bool | None = None,
    ) -> FailureAnalysis:
        from app.execution.models import TestExecution

        if not isinstance(execution, TestExecution):
            raise TypeError(f"Expected TestExecution, got {type(execution)}")

        input_data = AnalysisInput(
            test_name=execution.test_case_name,
            status=execution.status.value if hasattr(execution.status, "value") else str(execution.status),
            error_message=execution.error_message,
            logs=[l.message for l in execution.logs] if execution.logs else [],
            execution_id=execution.id,
            execution_type=execution.execution_type.value if hasattr(execution.execution_type, "value") else "unknown",
            duration_ms=execution.duration_ms,
            retry_count=execution.summary.retries_used if execution.summary else 0,
            tags=execution.tags,
        )

        return await self.analyze_failure(input_data, use_ai=use_ai)

    def set_ai_client(self, ai_client) -> None:
        self._ai_client = ai_client
        self._analyzer._ai_client = ai_client
        self._analyzer.screenshot_analyzer._ai_client = ai_client
