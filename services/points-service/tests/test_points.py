import pytest
from httpx import AsyncClient, ASGITransport
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
            assert data["service"] == "points-service"

    @pytest.mark.asyncio
    async def test_health_ready(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            assert response.status_code in (200, 503)

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


class TestPointsAPI:

    @pytest.mark.asyncio
    async def test_add_points_successfully(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/points/add",
                json={
                    "user_id": 1001,
                    "points": 50,
                    "source": "test",
                    "description": "test add points"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["change"] == 50
            assert data["balance_after"] == 50

    @pytest.mark.asyncio
    async def test_deduct_points_successfully(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            await client.post(
                "/api/v1/points/add",
                json={
                    "user_id": 1002,
                    "points": 100,
                    "source": "test",
                    "description": "setup balance"
                }
            )
            response = await client.post(
                "/api/v1/points/deduct",
                json={
                    "user_id": 1002,
                    "points": 30,
                    "source": "test",
                    "description": "test deduct"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["change"] == -30
            assert data["balance_after"] == 70

    @pytest.mark.asyncio
    async def test_deduct_points_insufficient_balance(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/points/deduct",
                json={
                    "user_id": 1003,
                    "points": 9999,
                    "source": "test",
                    "description": "test insufficient"
                }
            )
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_points_history(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            await client.post(
                "/api/v1/points/add",
                json={
                    "user_id": 1004,
                    "points": 20,
                    "source": "test",
                    "description": "history setup"
                }
            )
            response = await client.get(
                "/api/v1/points/history",
                params={"user_id": 1004}
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data

    @pytest.mark.asyncio
    async def test_get_points_history_pagination(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/points/history",
                params={"user_id": 1004, "page": 1, "page_size": 5}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 1
            assert data["page_size"] == 5

    @pytest.mark.asyncio
    async def test_daily_check_in(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/points/check-in",
                json={"user_id": 1005}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["checked_in"] is True
            assert data["points_awarded"] > 0
            assert data["current_streak"] >= 1

    @pytest.mark.asyncio
    async def test_duplicate_check_in_returns_error(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            await client.post(
                "/api/v1/points/check-in",
                json={"user_id": 1006}
            )
            response = await client.post(
                "/api/v1/points/check-in",
                json={"user_id": 1006}
            )
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_check_in_status(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/points/check-in/status",
                params={"user_id": 1005}
            )
            assert response.status_code == 200
            data = response.json()
            assert "checked_in_today" in data
            assert "current_streak" in data

    @pytest.mark.asyncio
    async def test_list_mall_items(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/points/mall")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data

    @pytest.mark.asyncio
    async def test_exchange_item_insufficient_points(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/points/mall/999/exchange",
                json={"user_id": 1007}
            )
            assert response.status_code in (400, 404)

    @pytest.mark.asyncio
    async def test_get_balance_new_user(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/points/9999")
            assert response.status_code == 200
            data = response.json()
            assert data["balance"] == 0
            assert data["total_earned"] == 0
            assert data["total_spent"] == 0
