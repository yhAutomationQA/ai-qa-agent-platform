from __future__ import annotations

import re
from textwrap import dedent


def clean_code_block(raw: str) -> str:
    """Extract code from markdown code fences and normalize indentation."""
    raw = raw.strip()
    pattern = r"```(?:typescript|javascript|ts|js)?\s*\n?(.*?)```"
    match = re.search(pattern, raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    return dedent(raw)


def format_ts_code(code: str, indent_size: int = 2) -> str:
    """Basic TypeScript code formatting: clean extra blank lines."""
    lines = code.split("\n")
    cleaned = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 1:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(line)
    return "\n".join(cleaned)


def sanitize_filename(name: str) -> str:
    """Convert a feature name to a valid filename."""
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = name.strip("-")
    return name or "test"


def build_context_block(input_data: "TestGenerationInput") -> str:
    """Build a structured context string from the input for prompt consumption."""
    parts = [f"## Requirement Summary\n{input_data.requirement_summary}"]

    if input_data.acceptance_criteria:
        criteria = "\n".join(f"- {ac}" for ac in input_data.acceptance_criteria)
        parts.append(f"## Acceptance Criteria\n{criteria}")

    if input_data.user_flows:
        flows = []
        for flow in input_data.user_flows:
            steps = "\n".join(f"  {i+1}. {s.action}" for i, s in enumerate(flow.steps))
            outcomes = "\n".join(f"  - {o}" for o in flow.expected_outcomes)
            flows.append(f"### {flow.name}\n{flow.description}\n\nSteps:\n{steps}\n\nExpected:\n{outcomes}")
        parts.append("## User Flows\n" + "\n\n".join(flows))

    if input_data.additional_context:
        parts.append(f"## Additional Context\n{input_data.additional_context}")

    parts.append(f"## Technology Stack\n{input_data.technology_stack.value}")

    return "\n\n".join(parts)
