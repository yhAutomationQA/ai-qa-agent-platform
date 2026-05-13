import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.exceptions import NotFoundError, ValidationError


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_404_error_format(self, client: AsyncClient):
        response = await client.get("/api/v1/agents/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_validation_error_format(self, client: AsyncClient):
        response = await client.post("/api/v1/agents", json={})
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_unhandled_exception_format(self, client: AsyncClient):
        response = await client.get("/trigger-error")
        assert response.status_code == 404


class TestMiddlewareStack:
    @pytest.mark.asyncio
    async def test_cors_expose_headers(self, client: AsyncClient):
        response = await client.get(
            "/api/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert "access-control-expose-headers" in response.headers
        assert "X-Request-ID" in response.headers["access-control-expose-headers"]

    @pytest.mark.asyncio
    async def test_response_time_header(self, client: AsyncClient):
        response = await client.get("/api/health")
        assert "x-response-time-ms" in response.headers
        ms = float(response.headers["x-response-time-ms"])
        assert ms > 0
