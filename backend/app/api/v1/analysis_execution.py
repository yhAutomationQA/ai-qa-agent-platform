from fastapi import APIRouter, HTTPException, Query
from typing import Any

from app.analysis.models import (
    AnalysisInput,
    BatchAnalysisInput,
    FailureAnalysis,
    BatchAnalysisResult,
)
from app.analysis.service import AnalysisService

router = APIRouter()


_service: AnalysisService | None = None


def get_service() -> AnalysisService:
    global _service
    if _service is None:
        try:
            from ai_orchestrator.llm.client import LLMClient
            client = LLMClient()
            _service = AnalysisService(ai_client=client)
        except Exception:
            _service = AnalysisService(ai_client=None)
    return _service


@router.post("/analyze", response_model=FailureAnalysis)
async def analyze_failure(
    input_data: AnalysisInput,
    use_ai: bool | None = Query(None, description="Enable AI-powered analysis"),
):
    service = get_service()
    return await service.analyze_failure(input_data, use_ai=use_ai)


@router.post("/analyze/batch", response_model=BatchAnalysisResult)
async def analyze_batch(
    batch: BatchAnalysisInput,
    use_ai: bool | None = Query(None, description="Enable AI-powered analysis"),
):
    service = get_service()
    return await service.analyze_batch(batch, use_ai=use_ai)


@router.post("/analyze/from-execution", response_model=FailureAnalysis)
async def analyze_from_execution(
    execution_id: str = Query(..., description="Execution ID to analyze"),
    use_ai: bool | None = Query(None),
):
    try:
        from app.execution.runner import TestExecutionEngine
        from app.execution.storage import ExecutionStorage

        storage = ExecutionStorage()
        execution_path = storage._run_dir(execution_id) / "execution_result.json"
        if execution_path.exists():
            import json
            with open(execution_path) as f:
                data = json.load(f)
            from app.execution.models import TestExecution
            execution = TestExecution(**data)
        else:
            raise FileNotFoundError(f"No execution result found for {execution_id}")

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    service = get_service()
    return await service.analyze_from_execution(execution, use_ai=use_ai)


@router.get("/config")
async def get_analysis_config():
    from app.analysis.config import analysis_settings
    return analysis_settings.model_dump()
