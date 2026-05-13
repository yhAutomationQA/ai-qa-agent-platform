import asyncio
import json
import time
from typing import Any

from app.analysis.config import analysis_settings
from app.analysis.models import (
    AnalysisInput,
    BatchAnalysisInput,
    FailureAnalysis,
    BatchAnalysisResult,
    RootCauseSuggestion,
    FailureCategoryResult,
    RiskAssessment,
    RetryRecommendation,
    AnalysisSummary,
    FailureCategory,
    RiskLevel,
)
from app.analysis.categorizer import FailureCategorizer
from app.analysis.risk_analyzer import RiskAnalyzer
from app.analysis.retry_advisor import RetryAdvisor
from app.analysis.summary_generator import SummaryGenerator
from app.analysis.screenshot_analyzer import ScreenshotAnalyzer
from app.analysis.prompts import (
    ROOT_CAUSE_SYSTEM_PROMPT,
    ROOT_CAUSE_USER_PROMPT,
    CATEGORY_SYSTEM_PROMPT,
    CATEGORY_USER_PROMPT,
    RISK_SYSTEM_PROMPT,
    RISK_USER_PROMPT,
    RETRY_SYSTEM_PROMPT,
    RETRY_USER_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
    SUMMARY_USER_PROMPT,
)


class ResultAnalyzer:
    def __init__(self, ai_client=None):
        self.categorizer = FailureCategorizer()
        self.risk_analyzer = RiskAnalyzer()
        self.retry_advisor = RetryAdvisor()
        self.summary_generator = SummaryGenerator()
        self.screenshot_analyzer = ScreenshotAnalyzer(ai_client)
        self._ai_client = ai_client

    async def analyze(
        self,
        input_data: AnalysisInput,
        use_ai: bool | None = None,
    ) -> FailureAnalysis:
        start = time.monotonic()
        use_ai = analysis_settings.ANALYSIS_ENABLE_AI if use_ai is None else use_ai
        ai_used = False
        ai_fallback = False

        category_result = self.categorizer.categorize(input_data)

        if use_ai and self._ai_client is not None:
            try:
                ai_root_cause = await self._analyze_root_cause_ai(input_data)
                ai_category = await self._analyze_category_ai(input_data, category_result)
                ai_risk = await self._analyze_risk_ai(input_data, category_result)
                ai_retry = await self._analyze_retry_ai(input_data, category_result)
                ai_summary = await self._analyze_summary_ai(
                    input_data, ai_root_cause, ai_category, ai_risk, ai_retry
                )

                category_result = self.categorizer.merge_ai_result(
                    category_result, ai_category
                )

                root_cause = ai_root_cause
                risk = ai_risk
                retry = ai_retry
                summary = ai_summary
                ai_used = True

            except Exception:
                if analysis_settings.ANALYSIS_AI_FALLBACK:
                    ai_fallback = True
                else:
                    raise

        if not ai_used:
            root_cause = self._analyze_root_cause_pattern(input_data)
            risk = self.risk_analyzer.analyze(input_data, category_result)
            retry = self.retry_advisor.recommend(input_data, category_result)
            summary = self.summary_generator.generate(
                input_data, root_cause, category_result, risk, retry
            )

        duration_ms = (time.monotonic() - start) * 1000

        return FailureAnalysis(
            input=input_data,
            root_cause=root_cause,
            category=category_result,
            risk=risk,
            retry=retry,
            summary=summary,
            ai_used=ai_used,
            ai_fallback=ai_fallback,
            duration_ms=round(duration_ms, 2),
        )

    async def analyze_batch(
        self,
        batch: BatchAnalysisInput,
        use_ai: bool | None = None,
    ) -> BatchAnalysisResult:
        start = time.monotonic()
        max_items = analysis_settings.ANALYSIS_MAX_SUMMARIES
        failures = batch.failures[:max_items]

        analyses = await asyncio.gather(
            *[self.analyze(f, use_ai=use_ai) for f in failures]
        )

        cat_dist: dict[str, int] = {}
        risk_dist: dict[str, int] = {}
        all_risks: list[RiskAssessment] = []
        all_retry: list[RetryRecommendation] = []
        top_issues: list[str] = []

        for a in analyses:
            cat = a.category.primary_category.value
            cat_dist[cat] = cat_dist.get(cat, 0) + 1

            rl = a.risk.level.value
            risk_dist[rl] = risk_dist.get(rl, 0) + 1

            all_risks.append(a.risk)
            all_retry.append(a.retry)

            if a.summary.one_liner:
                top_issues.append(a.summary.one_liner)

        top_issues.sort(
            key=lambda x: (
                0 if any(w in x.lower() for w in ["critical", "high"]) else 1
            )
        )

        overall_risk = self.risk_analyzer.aggregate_risk(all_risks)

        retry_summary = {
            "should_retry_count": sum(1 for r in all_retry if r.should_retry),
            "should_not_retry_count": sum(1 for r in all_retry if not r.should_retry),
            "average_suggested_retries": round(
                sum(r.suggested_max_retries for r in all_retry) / max(len(all_retry), 1), 1
            ),
        }

        analysis_duration_ms = (time.monotonic() - start) * 1000

        return BatchAnalysisResult(
            analyses=analyses,
            category_distribution=cat_dist,
            risk_distribution=risk_dist,
            overall_risk=overall_risk.level,
            top_issues=top_issues[:10],
            retry_summary=retry_summary,
            total_analyzed=len(analyses),
            analysis_duration_ms=round(analysis_duration_ms, 2),
        )

    def _analyze_root_cause_pattern(
        self,
        input_data: AnalysisInput,
    ) -> RootCauseSuggestion:
        evidence: list[str] = []
        title = "Unknown failure"
        description = "Could not determine root cause from available data."
        suggested_fix: str | None = None

        if input_data.error_message:
            evidence.append(f"Error: {input_data.error_message[:200]}")
            title = input_data.error_message.split("\n")[0][:100]
            description = f"Test failed with error: {input_data.error_message[:500]}"

        if input_data.stack_trace:
            frames = [
                l.strip() for l in input_data.stack_trace.split("\n")
                if 'File "' in l or '  at ' in l
            ]
            if frames:
                evidence.append(f"Stack trace: {frames[0][:200]}")

        if input_data.logs:
            last = input_data.logs[-1] if input_data.logs else ""
            if last:
                evidence.append(f"Last log: {last[:200]}")

        return RootCauseSuggestion(
            title=title,
            description=description,
            confidence=0.5 if input_data.error_message else 0.2,
            evidence=evidence[:5],
            suggested_fix=suggested_fix,
        )

    async def _analyze_root_cause_ai(
        self,
        input_data: AnalysisInput,
    ) -> RootCauseSuggestion:
        prompt = ROOT_CAUSE_USER_PROMPT.format(
            test_name=input_data.test_name or "N/A",
            test_suite=input_data.test_suite or "N/A",
            status=input_data.status or "failed",
            execution_type=input_data.execution_type or "N/A",
            duration_ms=input_data.duration_ms or "N/A",
            retry_count=input_data.retry_count or 0,
            error_message=input_data.error_message or "N/A",
            stack_trace=self._truncate(input_data.stack_trace, 2000) or "N/A",
            logs=self._truncate("\n".join(input_data.logs), 3000) or "N/A",
            api_response=self._truncate(input_data.api_response, 500) or "N/A",
            api_status_code=input_data.api_status_code or "N/A",
            api_request_url=input_data.api_request_url or "N/A",
            api_request_body=self._truncate(input_data.api_request_body, 500) or "N/A",
            tags=", ".join(input_data.tags) or "none",
        )

        response = await self._ai_client.generate(
            prompt=prompt[:analysis_settings.ANALYSIS_MAX_INPUT_LENGTH],
            system_prompt=ROOT_CAUSE_SYSTEM_PROMPT,
        )

        return self._parse_ai_response(response.content, RootCauseSuggestion)

    async def _analyze_category_ai(
        self,
        input_data: AnalysisInput,
        pattern_result: FailureCategoryResult,
    ) -> FailureCategoryResult | None:
        if not self.categorizer.requires_ai(pattern_result):
            return None

        prompt = CATEGORY_USER_PROMPT.format(
            error_message=input_data.error_message or "N/A",
            stack_trace=self._truncate(input_data.stack_trace, 1500) or "N/A",
            logs_tail=self._truncate("\n".join(input_data.logs[-20:]), 2000) or "N/A",
            api_response=self._truncate(input_data.api_response, 500) or "N/A",
            api_status_code=input_data.api_status_code or "N/A",
            duration_ms=input_data.duration_ms or "N/A",
            retry_count=input_data.retry_count or 0,
        )

        response = await self._ai_client.generate(
            prompt=prompt,
            system_prompt=CATEGORY_SYSTEM_PROMPT,
        )

        raw = self._parse_ai_json(response.content)
        if raw is None:
            return None

        try:
            primary = FailureCategory(raw.get("primary_category", "unknown"))
            secondary = [
                FailureCategory(c) for c in raw.get("secondary_categories", [])
                if c in FailureCategory._value2member_map_
            ]
            return FailureCategoryResult(
                primary_category=primary,
                secondary_categories=secondary,
                confidence=float(raw.get("confidence", 0.5)),
                reasoning=raw.get("reasoning", ""),
            )
        except (ValueError, TypeError):
            return None

    async def _analyze_risk_ai(
        self,
        input_data: AnalysisInput,
        category_result: FailureCategoryResult,
    ) -> RiskAssessment:
        prompt = RISK_USER_PROMPT.format(
            test_name=input_data.test_name or "N/A",
            category=category_result.primary_category.value,
            error_message=self._truncate(input_data.error_message, 500) or "N/A",
            stack_trace_length=len(input_data.stack_trace or ""),
            duration_ms=input_data.duration_ms or "N/A",
            retry_count=input_data.retry_count or 0,
            tags=", ".join(input_data.tags) or "none",
            execution_type=input_data.execution_type or "N/A",
            api_status_code=input_data.api_status_code or "N/A",
        )

        response = await self._ai_client.generate(
            prompt=prompt,
            system_prompt=RISK_SYSTEM_PROMPT,
        )

        raw = self._parse_ai_json(response.content)
        if raw is None:
            return self.risk_analyzer.analyze(input_data, category_result)

        try:
            return RiskAssessment(
                level=RiskLevel(raw.get("level", "low")),
                score=float(raw.get("score", 0.3)),
                impacted_areas=raw.get("impacted_areas", []),
                blast_radius=raw.get("blast_radius", ""),
                reasoning=raw.get("reasoning", ""),
            )
        except (ValueError, TypeError):
            return self.risk_analyzer.analyze(input_data, category_result)

    async def _analyze_retry_ai(
        self,
        input_data: AnalysisInput,
        category_result: FailureCategoryResult,
    ) -> RetryRecommendation:
        prompt = RETRY_USER_PROMPT.format(
            category=category_result.primary_category.value,
            error_message=self._truncate(input_data.error_message, 500) or "N/A",
            stack_trace_snippet=self._truncate(input_data.stack_trace, 500) or "N/A",
            duration_ms=input_data.duration_ms or "N/A",
            retry_count=input_data.retry_count or 0,
        )

        response = await self._ai_client.generate(
            prompt=prompt,
            system_prompt=RETRY_SYSTEM_PROMPT,
        )

        raw = self._parse_ai_json(response.content)
        if raw is None:
            return self.retry_advisor.recommend(input_data, category_result)

        try:
            return RetryRecommendation(
                should_retry=bool(raw.get("should_retry", False)),
                confidence=float(raw.get("confidence", 0.5)),
                reason=raw.get("reason", ""),
                suggested_max_retries=int(raw.get("suggested_max_retries", 1)),
                suggested_delay_seconds=float(raw.get("suggested_delay_seconds", 2.0)),
                conditions=raw.get("conditions", []),
            )
        except (ValueError, TypeError):
            return self.retry_advisor.recommend(input_data, category_result)

    async def _analyze_summary_ai(
        self,
        input_data: AnalysisInput,
        root_cause: RootCauseSuggestion,
        category_result: FailureCategoryResult,
        risk: RiskAssessment,
        retry: RetryRecommendation,
    ) -> AnalysisSummary:
        prompt = SUMMARY_USER_PROMPT.format(
            test_name=input_data.test_name or "N/A",
            category=category_result.primary_category.value,
            root_cause=root_cause.title or "Unknown",
            risk_level=risk.level.value,
            should_retry="Yes" if retry.should_retry else "No",
            description=root_cause.description or "N/A",
            suggested_fix=root_cause.suggested_fix or "Not available",
        )

        response = await self._ai_client.generate(
            prompt=prompt,
            system_prompt=SUMMARY_SYSTEM_PROMPT,
        )

        raw = self._parse_ai_json(response.content)
        if raw is None:
            return self.summary_generator.generate(
                input_data, root_cause, category_result, risk, retry
            )

        try:
            return AnalysisSummary(
                one_liner=raw.get("one_liner", ""),
                detailed_summary=raw.get("detailed_summary", ""),
                key_findings=raw.get("key_findings", []),
                recommended_actions=raw.get("recommended_actions", []),
                severity=RiskLevel(raw.get("severity", "low")),
            )
        except (ValueError, TypeError):
            return self.summary_generator.generate(
                input_data, root_cause, category_result, risk, retry
            )

    @staticmethod
    def _parse_ai_json(content: str) -> dict | None:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        import re
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def _parse_ai_response(
        content: str,
        model_class: type,
    ) -> Any:
        raw = ResultAnalyzer._parse_ai_json(content)
        if raw is None:
            return model_class()

        try:
            return model_class(**raw)
        except (ValueError, TypeError):
            return model_class()

    @staticmethod
    def _truncate(text: str | None, max_chars: int) -> str | None:
        if text is None:
            return None
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."
