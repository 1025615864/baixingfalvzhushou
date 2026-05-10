import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app

INTERNAL_API_KEY = "internal-api-key-change-in-production"


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
            assert "model_loaded" in data
            assert "model_name" in data
            assert "device" in data

    @pytest.mark.asyncio
    async def test_health_ready(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["ready", "not_ready"]

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


class TestRootEndpoint:

    @pytest.mark.asyncio
    async def test_root(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "embedding-service"
            assert data["version"] == "1.0.0"
            assert "model" in data
            assert "dimension" in data
            assert "device" in data
            assert "model_loaded" in data


class TestEmbeddingAPI:

    @pytest.mark.asyncio
    async def test_embed_texts(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/texts",
                json={"texts": ["法律咨询", "合同纠纷"]},
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            assert response.status_code == 200
            data = response.json()
            assert "embeddings" in data
            assert "model" in data
            assert "dimension" in data
            assert "usage_count" in data
            assert data["usage_count"] == 2
            assert len(data["embeddings"]) == 2

    @pytest.mark.asyncio
    async def test_embed_query(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/query",
                json={"query": "如何起诉离婚"},
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            assert response.status_code == 200
            data = response.json()
            assert "embedding" in data
            assert "model" in data
            assert "dimension" in data
            assert isinstance(data["embedding"], list)

    @pytest.mark.asyncio
    async def test_batch_embed(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/batch",
                json={
                    "texts": ["劳动仲裁", "房产纠纷", "交通事故"],
                    "batch_size": 2,
                },
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            assert response.status_code == 200
            data = response.json()
            assert "embeddings" in data
            assert "model" in data
            assert "dimension" in data
            assert "total_count" in data
            assert "batch_size" in data
            assert "batch_count" in data
            assert data["total_count"] == 3
            assert data["batch_size"] == 2
            assert data["batch_count"] == 2
            assert len(data["embeddings"]) == 3

    @pytest.mark.asyncio
    async def test_compute_similarity(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/similarity",
                json={"text1": "合同纠纷", "text2": "合同争议"},
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            assert response.status_code == 200
            data = response.json()
            assert "similarity" in data
            assert "model" in data
            assert "dimension" in data
            assert isinstance(data["similarity"], float)
            assert -1.0 <= data["similarity"] <= 1.0

    @pytest.mark.asyncio
    async def test_vector_search(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/search",
                json={
                    "query": "劳动法",
                    "candidates": ["劳动合同", "房产交易", "刑事辩护", "劳动仲裁", "公司注册"],
                    "top_k": 3,
                },
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            assert response.status_code == 200
            data = response.json()
            assert "query" in data
            assert "results" in data
            assert "model" in data
            assert "dimension" in data
            assert "total_candidates" in data
            assert data["total_candidates"] == 5
            assert len(data["results"]) <= 3
            for result in data["results"]:
                assert "index" in result
                assert "text" in result
                assert "score" in result


class TestEmbeddingAuth:

    @pytest.mark.asyncio
    async def test_embed_texts_without_api_key(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/texts",
                json={"texts": ["测试文本"]}
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_embed_texts_with_invalid_api_key(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/texts",
                json={"texts": ["测试文本"]},
                headers={"X-Internal-API-Key": "invalid-key"}
            )
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_embed_query_without_api_key(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/query",
                json={"query": "测试查询"}
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_similarity_without_api_key(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/similarity",
                json={"text1": "文本1", "text2": "文本2"}
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_search_without_api_key(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/search",
                json={"query": "查询", "candidates": ["候选1"]}
            )
            assert response.status_code == 401


class TestEmbeddingValidation:

    @pytest.mark.asyncio
    async def test_embed_empty_texts(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/texts",
                json={"texts": []},
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            assert response.status_code in [200, 422, 500]

    @pytest.mark.asyncio
    async def test_similarity_identical_texts(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/similarity",
                json={"text1": "合同纠纷", "text2": "合同纠纷"},
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            assert response.status_code == 200
            data = response.json()
            assert "similarity" in data
            if data["similarity"] > 0.5:
                assert abs(data["similarity"] - 1.0) < 0.05

    @pytest.mark.asyncio
    async def test_search_returns_ranked_results(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/search",
                json={
                    "query": "劳动法咨询",
                    "candidates": ["劳动合同法解读", "房产买卖指南", "劳动争议处理"],
                    "top_k": 3,
                },
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) > 0
            scores = [r["score"] for r in data["results"]]
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1]

    @pytest.mark.asyncio
    async def test_batch_embed_with_large_batch_size(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/batch",
                json={
                    "texts": ["文本1", "文本2"],
                    "batch_size": 512,
                },
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["embeddings"]) == 2

    @pytest.mark.asyncio
    async def test_search_with_top_k_exceeding_candidates(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/embeddings/search",
                json={
                    "query": "法律咨询",
                    "candidates": ["合同法", "刑法"],
                    "top_k": 10,
                },
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) <= 2
