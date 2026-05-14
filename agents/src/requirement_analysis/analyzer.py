import structlog
import time
from typing import Any

from agents.src.requirement_analysis.models import (
    RequirementAnalysisInput,
    RequirementAnalysisOutput,
    AnalysisMetadata,
    ParsedSections,
)
from agents.src.requirement_analysis.parsing import ResponseParser
from agents.src.requirement_analysis.prompts import (
    SYSTEM_PROMPT,
    REQUIREMENT_ANALYSIS_TEMPLATE,
    FIX_ERROR_PROMPT,
)

logger = structlog.get_logger()


class RequirementAnalyzer:
    def __init__(self, llm_client: Any, max_parse_retries: int = 2):
        self.llm = llm_client
        self.max_parse_retries = max_parse_retries
        self.parser = ResponseParser()

    async def analyze(self, input_data: RequirementAnalysisInput) -> RequirementAnalysisOutput:
        logger.info("requirement_analysis_started", issue_key=input_data.issue_key)
        start = time.time()

        prompt = self._build_prompt(input_data)
        parsed_sections, raw_response = await self._generate_and_parse(prompt)

        if ResponseParser.has_critical_failures(parsed_sections):
            logger.warning(
                "critical_parse_failures",
                validation={k: v.model_dump() for k, v in parsed_sections.validation.items()},
            )

        elapsed = (time.time() - start) * 1000

        output = self._to_output(parsed_sections, input_data, elapsed)
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

    async def _generate_and_parse(
        self,
        prompt: str,
    ) -> tuple[ParsedSections, Any]:
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.2,
        )

        raw_result = self.parser.extract_json(response.content)
        parsed_sections = self.parser.validate_sections(raw_result.parsed_data)

        retries = 0
        while (
            ResponseParser.has_critical_failures(parsed_sections)
            and raw_result.parse_error
            and retries < self.max_parse_retries
        ):
            retries += 1
            logger.info(
                "retrying_parse",
                attempt=retries,
                max_retries=self.max_parse_retries,
                error=raw_result.parse_error,
            )

            feedback = self.parser.build_error_feedback(raw_result, parsed_sections)
            fix_prompt = f"{prompt}\n\n{feedback}"

            response = await self.llm.generate(
                prompt=fix_prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.3,
            )

            raw_result = self.parser.extract_json(response.content)
            parsed_sections = self.parser.validate_sections(raw_result.parsed_data)

        return parsed_sections, raw_result

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

    def _to_output(
        self,
        parsed_sections: ParsedSections,
        input_data: RequirementAnalysisInput,
        elapsed_ms: float,
    ) -> RequirementAnalysisOutput:
        metadata = AnalysisMetadata(
            model_used=self.llm.model_name,
            total_tokens=0,
            processing_time_ms=round(elapsed_ms, 2),
            source_issue_key=input_data.issue_key,
        )

        return RequirementAnalysisOutput(
            summary=parsed_sections.summary,
            functional_scenarios=parsed_sections.functional_scenarios,
            edge_cases=parsed_sections.edge_cases,
            negative_scenarios=parsed_sections.negative_scenarios,
            risk_areas=parsed_sections.risk_areas,
            missing_requirements=parsed_sections.missing_requirements,
            metadata=metadata,
        )
