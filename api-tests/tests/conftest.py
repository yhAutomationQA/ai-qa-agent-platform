import pytest
from typing import Generator

from api_tests.src.helpers.client import APITestClient


@pytest.fixture(scope="session")
def api_client() -> Generator[APITestClient, None, None]:
    client = APITestClient(
        base_url="http://localhost:8000/api/v1",
        timeout=30,
    )
    yield client
    client.close()
