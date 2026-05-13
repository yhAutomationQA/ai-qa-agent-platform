from typing import Any


def generate_agent_payload(name: str | None = None, agent_type: str = "browser") -> dict[str, Any]:
    return {
        "name": name or f"Test Agent {__import__('time').time()}",
        "description": "Auto-generated test agent",
        "agent_type": agent_type,
        "config": {"headless": True, "timeout": 30},
    }


def generate_test_case_payload(name: str | None = None, test_type: str = "ui") -> dict[str, Any]:
    return {
        "name": name or f"Test Case {__import__('time').time()}",
        "description": "Auto-generated test case",
        "test_type": test_type,
        "parameters": {"url": "http://localhost:3000"},
        "tags": ["e2e", "smoke"],
    }


def generate_prompt_payload(name: str | None = None) -> dict[str, Any]:
    return {
        "name": name or f"Test Prompt {__import__('time').time()}",
        "description": "Auto-generated test prompt",
        "template": "You are a QA agent. Test the following: {{ scenario }}",
        "variables": ["scenario"],
        "tags": ["qa", "test-generation"],
    }
