import json
import re
import structlog
from typing import Any

from pydantic import ValidationError

from agents.src.requirement_analysis.models import (
    RequirementSummary,
    FunctionalScenario,
    EdgeCase,
    NegativeScenario,
    RiskArea,
    MissingRequirement,
    SectionValidation,
    ParsedSections,
    RawAIResponse,
)

logger = structlog.get_logger()


# List-based sections only (summary is handled separately)
_SECTION_MAP: dict[str, tuple[str, type]] = {
    "functional_scenarios": ("functional_scenarios", FunctionalScenario),
    "edge_cases": ("edge_cases", EdgeCase),
    "negative_scenarios": ("negative_scenarios", NegativeScenario),
    "risk_areas": ("risk_areas", RiskArea),
    "missing_requirements": ("missing_requirements", MissingRequirement),
}

# Models that have an auto-generated id field
_MODELS_WITH_ID = {FunctionalScenario, EdgeCase, NegativeScenario, MissingRequirement}


class ResponseParser:
    """Robust JSON extraction and validation from LLM responses."""

    @staticmethod
    def extract_json(raw: str) -> RawAIResponse:
        raw = raw or ""
        result = RawAIResponse(raw_text=raw, extracted_json="")

        cleaned = raw.strip()

        # 1. Remove markdown code fences
        cleaned = ResponseParser._strip_fences(cleaned)

        # 2. Try direct parse
        parsed, error = ResponseParser._try_parse(cleaned)
        if parsed is not None:
            result.extracted_json = cleaned
            result.parsed_data = parsed
            return result

        # 3. Try to find JSON object/array via regex
        extracted = ResponseParser._regex_extract(cleaned)
        if extracted:
            parsed, error = ResponseParser._try_parse(extracted)
            if parsed is not None:
                result.extracted_json = extracted
                result.parsed_data = parsed
                return result

        # 4. Try common JSON repairs
        repaired = ResponseParser._repair_json(cleaned)
        if repaired and repaired != cleaned:
            parsed, error = ResponseParser._try_parse(repaired)
            if parsed is not None:
                result.extracted_json = repaired
                result.parsed_data = parsed
                return result

        result.parse_error = error or "No valid JSON found in response"
        logger.warning("json_parse_failed", error=result.parse_error, text_length=len(raw))
        return result

    @staticmethod
    def validate_sections(data: dict[str, Any]) -> ParsedSections:
        validations: dict[str, SectionValidation] = {}
        sections: dict[str, Any] = {}

        for key, (section_name, model_class) in _SECTION_MAP.items():
            raw_items = data.get(key)
            section_result, validation = ResponseParser._validate_section(
                raw_items, model_class, section_name
            )
            sections[key] = section_result
            validations[key] = validation

        summary_data = data.get("summary", {})
        summary: RequirementSummary
        if isinstance(summary_data, dict):
            try:
                summary = RequirementSummary.model_validate(summary_data)
                validations["summary"] = SectionValidation(valid_count=1)
            except ValidationError as e:
                logger.warning("summary_validation_failed", errors=e.errors())
                summary = RequirementSummary()
                validations["summary"] = SectionValidation(
                    failed_count=1,
                    errors=[str(e) for e in e.errors()],
                )
        else:
            summary = RequirementSummary()
            validations["summary"] = SectionValidation(
                failed_count=1,
                errors=["summary must be an object"],
            )

        return ParsedSections(
            summary=summary,
            functional_scenarios=sections.get("functional_scenarios", []),
            edge_cases=sections.get("edge_cases", []),
            negative_scenarios=sections.get("negative_scenarios", []),
            risk_areas=sections.get("risk_areas", []),
            missing_requirements=sections.get("missing_requirements", []),
            validation=validations,
        )

    @staticmethod
    def has_critical_failures(parsed: ParsedSections) -> bool:
        for section_name, validation in parsed.validation.items():
            if section_name == "missing_requirements":
                continue
            if validation.valid_count == 0 and validation.failed_count > 0:
                if section_name == "summary":
                    return True
                if section_name != "risk_areas":
                    return True
        return False

    @staticmethod
    def build_error_feedback(raw_response: RawAIResponse, parsed: ParsedSections) -> str:
        lines = ["The previous response had JSON parsing or validation errors. Please fix:"]
        if raw_response.parse_error:
            lines.append(f"- Parse error: {raw_response.parse_error}")
        for section_name, v in parsed.validation.items():
            if v.failed_count > 0:
                lines.append(f"- Section '{section_name}': {v.failed_count} item(s) failed validation")
                for err in v.errors[:3]:
                    lines.append(f"  - {err}")
        return "\n".join(lines)

    # ── Internal helpers ──────────────────────────────────

    @staticmethod
    def _strip_fences(text: str) -> str:
        text = text.strip()
        fence_pattern = re.compile(
            r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL
        )
        match = fence_pattern.search(text)
        if match:
            return match.group(1).strip()
        if text.startswith("```"):
            text = re.sub(r"^```\w*\s*", "", text)
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    @staticmethod
    def _try_parse(text: str) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
        if not text:
            return None, "Empty text"
        try:
            result = json.loads(text)
            if isinstance(result, dict) or isinstance(result, list):
                return result, None
            return None, f"JSON value is type {type(result).__name__}, expected object/array"
        except json.JSONDecodeError as e:
            return None, str(e)

    @staticmethod
    def _regex_extract(text: str) -> str | None:
        for pattern in [r"(\{[\s\S]*\})", r"(\[[\s\S]*\])"]:
            match = re.search(pattern, text)
            if match:
                candidate = match.group(1)
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    continue
        return None

    @staticmethod
    def _repair_json(text: str) -> str | None:
        repairs = []

        # Remove trailing commas before closing brackets
        repaired = re.sub(r",\s*([}\]])", r"\1", text)
        if repaired != text:
            repairs.append("trailing commas")

        # Replace single quotes with double quotes (simple cases)
        # Only when it looks like a JSON-like structure
        if "'" in repaired and '"' not in repaired[:100]:
            repaired_sq = repaired.replace("'", '"')
            try:
                json.loads(repaired_sq)
                repairs.append("single→double quotes")
                return repaired_sq
            except json.JSONDecodeError:
                pass

        # Try wrapping unquoted keys
        wrapped = re.sub(
            r"(?<=\{|\s,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:",
            r'"\1":',
            repaired,
        )
        if wrapped != repaired:
            try:
                json.loads(wrapped)
                repairs.append("unquoted keys")
                return wrapped
            except json.JSONDecodeError:
                pass

        if repairs:
            return repaired
        return None

    @staticmethod
    def _validate_section(
        raw_items: Any,
        model_class: type,
        section_name: str,
    ) -> tuple[list[Any], SectionValidation]:
        if not isinstance(raw_items, list):
            logger.warning("section_not_a_list", section=section_name, type=type(raw_items).__name__)
            return [], SectionValidation(failed_count=1, errors=[f"expected list, got {type(raw_items).__name__}"])

        valid_items: list[Any] = []
        validation_errors: list[str] = []

        for i, item in enumerate(raw_items):
            if not isinstance(item, dict):
                validation_errors.append(f"[{i}] expected object, got {type(item).__name__}")
                continue
            try:
                validated = model_class.model_validate(item)
                # Assign auto-id if missing (for models that have an id field)
                if model_class in _MODELS_WITH_ID and not getattr(validated, 'id', None):
                    prefix = {
                        "functional_scenarios": "FS",
                        "edge_cases": "EC",
                        "negative_scenarios": "NS",
                        "risk_areas": "RA",
                        "missing_requirements": "MR",
                    }.get(section_name, "XX")
                    validated.id = f"{prefix}-{i + 1:02d}"
                valid_items.append(validated)
            except ValidationError as e:
                field_errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
                validation_errors.append(f"[{i}] {'; '.join(field_errors)}")
                logger.debug("item_validation_failed", section=section_name, index=i, errors=e.errors())

        return valid_items, SectionValidation(
            valid_count=len(valid_items),
            failed_count=len(raw_items) - len(valid_items),
            errors=validation_errors,
        )
