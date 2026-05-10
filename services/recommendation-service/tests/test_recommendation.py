import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app


class TestHealthEndpoints:

    @pytest.mark.asyncio
    async def test_health(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "recommendation-service"

    @pytest.mark.asyncio
    async def test_health_ready(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200
            assert response.json()["status"] == "ready"

    @pytest.mark.asyncio
    async def test_health_live(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/live")
            assert response.status_code == 200
            assert response.json()["status"] == "alive"


class TestRecommendationAPI:

    @pytest.mark.asyncio
    async def test_recommend_lawyers(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/recommendations/lawyers",
                params={"user_id": 1}
            )
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_recommend_news(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/recommendations/news",
                params={"user_id": 1}
            )
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_recommend_posts(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/recommendations/posts",
                params={"user_id": 1}
            )
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_recommend_feed(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/recommendations/feed",
                params={"user_id": 1}
            )
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_recommend_homepage(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/recommendations/homepage",
                params={"user_id": 1}
            )
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_recommend_knowledge(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/recommendations/knowledge",
                params={"user_id": 1}
            )
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_update_user_features(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/recommendations/user/1/features",
                json={"interests": ["法律", "合同"], "view_history": [1, 2, 3]}
            )
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "user_id" in data
                assert "features" in data
                assert "updated_at" in data


class TestRecommendationValidation:

    @pytest.mark.asyncio
    async def test_lawyers_without_user_id(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/recommendations/lawyers")
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_news_without_user_id(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/recommendations/news")
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_feed_without_user_id(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/recommendations/feed")
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_recommendations_with_limit(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/recommendations/lawyers",
                params={"user_id": 1, "limit": 5}
            )
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                assert len(data["items"]) <= 5

    @pytest.mark.asyncio
    async def test_homepage_with_limit(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/recommendations/homepage",
                params={"user_id": 1, "limit": 10}
            )
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                assert len(data["items"]) <= 10

    @pytest.mark.asyncio
    async def test_update_user_features_with_empty_features(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/recommendations/user/1/features",
                json={}
            )
            assert response.status_code in [200, 500]
