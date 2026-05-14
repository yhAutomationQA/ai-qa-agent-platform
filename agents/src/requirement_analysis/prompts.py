SYSTEM_PROMPT = """You are a senior QA engineer and requirement analyst. Your role is to analyze software requirements and produce structured JSON output. You ALWAYS return valid JSON only, with no markdown wrapping, no explanation, no code fences."""

FIX_ERROR_PROMPT = """The previous response had JSON parsing or validation errors. Fix the issues and return a corrected JSON object matching the exact schema below. Return ONLY the JSON, no markdown."""

REQUIREMENT_ANALYSIS_TEMPLATE = """Analyze the following user story and produce a comprehensive requirement analysis as a JSON object.

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

## Output JSON Schema

Produce a JSON object with EXACTLY these keys. No additional keys, no missing keys.

### 1. "summary" — object
```json
{{
  "overall_purpose": "One-sentence summary of what this story delivers",
  "key_functionality": ["array of 3-6 key functional aspects"],
  "stakeholders": ["array of inferred stakeholder roles"],
  "dependencies": ["array of implied dependencies"],
  "complexity": "medium"
}}
```
`complexity` must be one of: `"low"`, `"medium"`, `"high"`.

### 2. "functional_scenarios" — array of objects (generate 3-8)
```json
[
  {{
    "title": "Scenario name",
    "description": "What this scenario validates",
    "preconditions": ["list of setup conditions"],
    "steps": ["ordered list of step-by-step actions"],
    "expected_result": "What should happen",
    "relates_to_ac": "Which acceptance criterion this maps to",
    "priority": "high"
  }}
]
```
`priority` must be one of: `"high"`, `"medium"`, `"low"`.

### 3. "edge_cases" — array of objects (generate 2-5)
```json
[
  {{
    "title": "Edge case name",
    "description": "What edge condition is tested",
    "input_condition": "The boundary input or state",
    "expected_behavior": "Expected system response",
    "severity": "medium",
    "category": "boundary"
  }}
]
```
`severity`: one of `"critical"`, `"high"`, `"medium"`, `"low"`.
`category`: one of `"boundary"`, `"empty/null"`, `"format"`, `"concurrency"`, `"state"`, `"data_type"`.

### 4. "negative_scenarios" — array of objects (generate 2-4)
```json
[
  {{
    "title": "Scenario name",
    "description": "What negative condition is tested",
    "malicious_input": "The invalid or malicious input",
    "expected_failure": "The expected error or rejection",
    "attack_vector": "input_validation",
    "severity": "critical"
  }}
]
```
`attack_vector`: one of `"injection"`, `"auth_bypass"`, `"input_validation"`, `"business_logic"`, `"resource_exhaustion"`, `"protocol_violation"`.
`severity`: one of `"critical"`, `"high"`, `"medium"`, `"low"`.

### 5. "risk_areas" — array of objects (generate 1-3)
```json
[
  {{
    "area": "Risk category name",
    "description": "What the risk is",
    "likelihood": "medium",
    "impact": "high",
    "mitigation": "Suggested mitigation strategy"
  }}
]
```
`likelihood`, `impact`: each one of `"low"`, `"medium"`, `"high"`.

### 6. "missing_requirements" — array of objects (generate 0-3)
```json
[
  {{
    "title": "What is missing",
    "description": "Detail about the gap",
    "rationale": "Why this matters",
    "suggested_action": "What to propose to the product owner",
    "priority": "medium"
  }}
]
```
`priority`: one of `"high"`, `"medium"`, `"low"`.

---

Return ONLY the JSON object. No preamble, no explanation, no code fences. No trailing commas. No comments in JSON."""
