import json
import structlog
import time
from typing import Any

from agents.src.requirement_analysis.models import (
    RequirementAnalysisInput,
    RequirementAnalysisOutput,
    RequirementSummary,
    FunctionalScenario,
    EdgeCase,
    NegativeScenario,
    RiskArea,
    MissingRequirement,
    AnalysisMetadata,
)
from agents.src.requirement_analysis.prompts import (
    SYSTEM_PROMPT,
    REQUIREMENT_ANALYSIS_TEMPLATE,
)

logger = structlog.get_logger()


class RequirementAnalyzer:
    def __init__(self, llm_client: Any):
        self.llm = llm_client

    async def analyze(self, input_data: RequirementAnalysisInput) -> RequirementAnalysisOutput:
        logger.info("requirement_analysis_started", issue_key=input_data.issue_key)
        start = time.time()

        prompt = self._build_prompt(input_data)
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.2,
        )

        raw = self._clean_response(response.content)
        parsed = json.loads(raw)
        elapsed = (time.time() - start) * 1000

        output = self._to_output(parsed, input_data, response, elapsed)
        logger.info(
            "requirement_analysis_completed",
            issue_key=input_data.issue_key,
            scenarios=len(output.functional_scenarios),
            edge_cases=len(output.edge_cases),
            negative=len(output.negative_scenarios),
            risks=len(output.risk_areas),
            gaps=len(output.missing_requirements),
            duration_ms=round(elapsed, 1),
        )
        return output

    def _build_prompt(self, input_data: RequirementAnalysisInput) -> str:
        ac_text = "\n".join(f"- {ac}" for ac in input_data.acceptance_criteria) or "(none provided)"
        comments_text = "\n".join(
            f"- {c.get('author', {}).get('displayName', 'Unknown')}: {c.get('body', '')[:300]}"
            for c in input_data.comments
        ) or "(none)"

        return REQUIREMENT_ANALYSIS_TEMPLATE.format(
            issue_key=input_data.issue_key,
            summary=input_data.summary,
            description=input_data.description or "(no description provided)",
            priority=input_data.priority or "unspecified",
            labels=", ".join(input_data.labels) or "(none)",
            acceptance_criteria=ac_text,
            comments=comments_text,
        )

    def _clean_response(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _to_output(
        self,
        parsed: dict[str, Any],
        input_data: RequirementAnalysisInput,
        response: Any,
        elapsed_ms: float,
    ) -> RequirementAnalysisOutput:
        summary_data = parsed.get("summary", {})
        summary = RequirementSummary(
            overall_purpose=summary_data.get("overall_purpose", ""),
            key_functionality=summary_data.get("key_functionality", []),
            stakeholders=summary_data.get("stakeholders", []),
            dependencies=summary_data.get("dependencies", []),
            complexity=summary_data.get("complexity", "medium"),
        )

        scenarios = [
            FunctionalScenario(
                id=f"FS-{i+1:02d}",
                title=s.get("title", ""),
                description=s.get("description", ""),
                preconditions=s.get("preconditions", []),
                steps=s.get("steps", []),
                expected_result=s.get("expected_result", ""),
                relates_to_ac=s.get("relates_to_ac", ""),
                priority=s.get("priority", "medium"),
            )
            for i, s in enumerate(parsed.get("functional_scenarios", []))
        ]

        edge_cases = [
            EdgeCase(
                id=f"EC-{i+1:02d}",
                title=e.get("title", ""),
                description=e.get("description", ""),
                input_condition=e.get("input_condition", ""),
                expected_behavior=e.get("expected_behavior", ""),
                severity=e.get("severity", "medium"),
                category=e.get("category", "boundary"),
            )
            for i, e in enumerate(parsed.get("edge_cases", []))
        ]

        negative_scenarios = [
            NegativeScenario(
                id=f"NS-{i+1:02d}",
                title=n.get("title", ""),
                description=n.get("description", ""),
                malicious_input=n.get("malicious_input", ""),
                expected_failure=n.get("expected_failure", ""),
                attack_vector=n.get("attack_vector", "input_validation"),
                severity=n.get("severity", "medium"),
            )
            for i, n in enumerate(parsed.get("negative_scenarios", []))
        ]

        risk_areas = [
            RiskArea(
                area=r.get("area", ""),
                description=r.get("description", ""),
                likelihood=r.get("likelihood", "medium"),
                impact=r.get("impact", "medium"),
                mitigation=r.get("mitigation", ""),
            )
            for r in parsed.get("risk_areas", [])
        ]

        missing_reqs = [
            MissingRequirement(
                title=m.get("title", ""),
                description=m.get("description", ""),
                rationale=m.get("rationale", ""),
                suggested_action=m.get("suggested_action", ""),
                priority=m.get("priority", "medium"),
            )
            for m in parsed.get("missing_requirements", [])
        ]

        token_usage = response.token_usage.total_tokens if response.token_usage else 0

        metadata = AnalysisMetadata(
            model_used=self.llm.model_name,
            total_tokens=token_usage,
            processing_time_ms=round(elapsed_ms, 2),
            source_issue_key=input_data.issue_key,
        )

        return RequirementAnalysisOutput(
            summary=summary,
            functional_scenarios=scenarios,
            edge_cases=edge_cases,
            negative_scenarios=negative_scenarios,
            risk_areas=risk_areas,
            missing_requirements=missing_reqs,
            metadata=metadata,
        )
