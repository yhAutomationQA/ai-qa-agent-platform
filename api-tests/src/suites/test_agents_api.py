import pytest
from api_tests.src.helpers.client import APITestClient
from api_tests.src.helpers.assertions import assert_status
from api_tests.src.fixtures.test_data import generate_agent_payload


@pytest.fixture
def client():
    c = APITestClient(base_url="http://localhost:8000/api/v1")
    yield c
    c.close()


class TestAgentsAPI:
    def test_create_agent(self, client: APITestClient):
        payload = generate_agent_payload()
        response = client.post("/agents", json=payload)
        assert_status(response, 201)
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["agent_type"] == payload["agent_type"]
        return data

    def test_list_agents(self, client: APITestClient):
        response = client.get("/agents")
        assert_status(response)
        assert isinstance(response.json(), list)

    def test_get_agent(self, client: APITestClient):
        created = self.test_create_agent(client)
        response = client.get(f"/agents/{created['id']}")
        assert_status(response)
        assert response.json()["id"] == created["id"]

    def test_delete_agent(self, client: APITestClient):
        created = self.test_create_agent(client)
        response = client.delete(f"/agents/{created['id']}")
        assert_status(response, 204)
