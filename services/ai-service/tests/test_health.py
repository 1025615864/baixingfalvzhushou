import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app


class TestHealthEndpoints:

    @pytest.mark.asyncio
    async def test_health(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "ai-service"

    @pytest.mark.asyncio
    async def test_health_ready(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"

    @pytest.mark.asyncio
    async def test_health_live(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/live")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "alive"
