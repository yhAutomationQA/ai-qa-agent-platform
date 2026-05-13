import pytest
from api_tests.src.helpers.client import APITestClient
from api_tests.src.helpers.assertions import assert_status


@pytest.fixture
def client():
    c = APITestClient(base_url="http://localhost:8000/api/v1")
    yield c
    c.close()


class TestHealthEndpoint:
    def test_health_check(self, client: APITestClient):
        response = client.get("/health")
        assert_status(response)
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-qa-platform"

    def test_database_health(self, client: APITestClient):
        response = client.get("/health/database")
        assert_status(response)
        assert response.json()["status"] == "healthy"
