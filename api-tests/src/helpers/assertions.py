from typing import Any
import httpx
from deepdiff import DeepDiff


def assert_status(response: httpx.Response, expected: int = 200) -> None:
    assert response.status_code == expected, (
        f"Expected status {expected}, got {response.status_code}: {response.text}"
    )


def assert_json_schema(response: httpx.Response, schema: dict) -> None:
    import jsonschema
    jsonschema.validate(instance=response.json(), schema=schema)


def assert_json_match(actual: dict, expected: dict, exclude_paths: list[str] | None = None) -> None:
    diff = DeepDiff(
        expected,
        actual,
        exclude_paths=exclude_paths or [],
        ignore_order=True,
    )
    assert not diff, f"JSON mismatch: {diff}"


def assert_pagination(response: httpx.Response) -> dict:
    data = response.json()
    assert isinstance(data, list) or "items" in data
    return data


def assert_error_response(response: httpx.Response, expected_status: int, expected_code: str | None = None) -> None:
    assert response.status_code == expected_status
    body = response.json()
    assert "detail" in body
    if expected_code and isinstance(body.get("detail"), dict):
        assert body["detail"].get("error_code") == expected_code
