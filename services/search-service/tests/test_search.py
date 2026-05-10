import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


class TestHealthEndpoints:

    @pytest.mark.asyncio
    async def test_health(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["service"] == "search-service"

    @pytest.mark.asyncio
    async def test_health_ready(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ("ready", "degraded")
            assert "checks" in data

    @pytest.mark.asyncio
    async def test_health_live(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/live")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "alive"


class TestSearchAPI:

    @pytest.mark.asyncio
    async def test_search_with_query(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/search/",
                params={"query": "离婚"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert data["query"] == "离婚"

    @pytest.mark.asyncio
    async def test_search_empty_query_returns_error(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/search/")
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_pagination(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/search/",
                params={"query": "合同", "page": 1, "page_size": 5}
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) <= 5

    @pytest.mark.asyncio
    async def test_search_by_type_valid(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/search/by-type/news",
                params={"query": "劳动"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert data["type"] == "news"

    @pytest.mark.asyncio
    async def test_search_by_type_invalid(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/search/by-type/invalid_type",
                params={"query": "劳动"}
            )
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_search_suggestions(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/search/suggestions",
                params={"query": "离"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_search_suggestions_with_limit(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/search/suggestions",
                params={"query": "合同", "limit": 3}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) <= 3

    @pytest.mark.asyncio
    async def test_hot_searches(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/search/hot",
                params={"limit": 5}
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_hot_searches_returns_default_keywords_when_db_empty(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/search/hot",
                params={"limit": 10}
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            if len(data["items"]) > 0:
                assert "keyword" in data["items"][0]
                assert "count" in data["items"][0]

    @pytest.mark.asyncio
    async def test_search_history(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/search/history",
                params={"user_id": 1}
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_search_history_with_limit(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/search/history",
                params={"user_id": 1, "limit": 5}
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) <= 5

    @pytest.mark.asyncio
    async def test_search_with_type_filter(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/search/",
                params={"query": "工伤", "type": "lawyer"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["type"] == "lawyer"
