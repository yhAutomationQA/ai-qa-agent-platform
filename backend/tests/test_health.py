import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestRoot:
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "version" in data
        assert data["docs"] == "/docs"


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-qa-platform-backend"

    @pytest.mark.asyncio
    async def test_liveness_endpoint(self, client: AsyncClient):
        response = await client.get("/api/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    @pytest.mark.asyncio
    async def test_readiness_endpoint_without_db(self, client: AsyncClient):
        response = await client.get("/api/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"


class TestCORS:
    @pytest.mark.asyncio
    async def test_cors_headers(self, client: AsyncClient):
        response = await client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


class TestRequestID:
    @pytest.mark.asyncio
    async def test_request_id_in_response(self, client: AsyncClient):
        response = await client.get("/api/health")
        assert "x-request-id" in response.headers
        assert "x-response-time-ms" in response.headers
