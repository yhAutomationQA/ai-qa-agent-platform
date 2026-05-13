SYSTEM_PROMPT = """You are a senior QA engineer and requirement analyst. Your role is to analyze software requirements and produce structured, actionable test analysis. Always return valid JSON only, with no markdown wrapping or additional text."""


REQUIREMENT_ANALYSIS_TEMPLATE = """Analyze the following user story and produce a comprehensive requirement analysis.

## User Story
**Key:** {issue_key}
**Summary:** {summary}
**Priority:** {priority}
**Labels:** {labels}

## Description
{description}

## Acceptance Criteria
{acceptance_criteria}

## Stakeholder Comments
{comments}

---

Produce a JSON object with exactly five keys. Follow the schema below strictly:

### 1. "summary" — object
- "overall_purpose": one-sentence summary of what this story delivers
- "key_functionality": array of 3-6 key functional aspects
- "stakeholders": array of inferred stakeholder roles
- "dependencies": array of implied dependencies
- "complexity": one of "low", "medium", "high" with brief justification

### 2. "functional_scenarios" — array of objects
Each object:
- "title": scenario name
- "description": what it validates
- "preconditions": array of setup conditions
- "steps": array of step-by-step actions
- "expected_result": what should happen
- "relates_to_ac": which acceptance criterion this maps to
- "priority": one of "high", "medium", "low"

Generate 3-8 functional scenarios covering happy path, alternate flows, and error handling.

### 3. "edge_cases" — array of objects
Each object:
- "title": edge case name
- "description": what edge condition is tested
- "input_condition": the boundary input or state
- "expected_behavior": expected system response
- "severity": one of "critical", "high", "medium", "low"
- "category": one of "boundary", "empty/null", "format", "concurrency", "state", "data_type"

Generate 2-5 edge cases.

### 4. "negative_scenarios" — array of objects
Each object:
- "title": scenario name
- "description": what negative condition is tested
- "malicious_input": the invalid or malicious input
- "expected_failure": the expected error or rejection
- "attack_vector": one of "injection", "auth_bypass", "input_validation", "business_logic", "resource_exhaustion", "protocol_violation"
- "severity": one of "critical", "high", "medium", "low"

Generate 2-4 negative scenarios.

### 5. "risk_areas" — array of objects
Each object:
- "area": risk category name
- "description": what the risk is
- "likelihood": one of "low", "medium", "high"
- "impact": one of "low", "medium", "high"
- "mitigation": suggested mitigation strategy

Generate 1-3 risk areas.

### 6. "missing_requirements" — array of objects
Each object:
- "title": what is missing
- "description": detail about the gap
- "rationale": why this matters
- "suggested_action": what to propose to the product owner
- "priority": one of "high", "medium", "low"

Generate 0-3 missing requirements if gaps are identified.

Return ONLY the JSON object. No preamble, no explanation, no code fences."""
