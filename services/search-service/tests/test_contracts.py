"""搜索服务契约测试"""
import pytest
from httpx import AsyncClient


class TestSearchServiceContract:
    """搜索服务契约测试"""

    @pytest.mark.asyncio
    async def test_global_search(self, client: AsyncClient):
        """测试全局搜索"""
        response = await client.get(
            "/api/v1/search/",
            params={"query": "法律咨询", "type": "all", "page": 1, "page_size": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "query" in data
        assert "type" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_search_news_only(self, client: AsyncClient):
        """测试仅搜索新闻"""
        response = await client.get(
            "/api/v1/search/",
            params={"query": "法律", "type": "news", "page": 1, "page_size": 10}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_posts_only(self, client: AsyncClient):
        """测试仅搜索帖子"""
        response = await client.get(
            "/api/v1/search/",
            params={"query": "讨论", "type": "post", "page": 1, "page_size": 10}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_lawyers_only(self, client: AsyncClient):
        """测试仅搜索律师"""
        response = await client.get(
            "/api/v1/search/",
            params={"query": "律师", "type": "lawyer", "page": 1, "page_size": 10}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_knowledge_only(self, client: AsyncClient):
        """测试仅搜索法律知识"""
        response = await client.get(
            "/api/v1/search/",
            params={"query": "法律知识", "type": "knowledge", "page": 1, "page_size": 10}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_suggestions(self, client: AsyncClient):
        """测试搜索建议"""
        response = await client.get(
            "/api/v1/search/suggestions",
            params={"query": "劳动"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_search_suggestions_with_limit(self, client: AsyncClient):
        """测试搜索建议带数量限制"""
        response = await client.get(
            "/api/v1/search/suggestions",
            params={"query": "合同", "limit": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5

    @pytest.mark.asyncio
    async def test_hot_searches(self, client: AsyncClient):
        """测试热门搜索"""
        response = await client.get(
            "/api/v1/search/hot",
            params={"limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) <= 10

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, client: AsyncClient):
        """测试搜索分页"""
        response = await client.get(
            "/api/v1/search/",
            params={"query": "法律", "page": 2, "page_size": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "法律"


class TestSearchServiceModelsContract:
    """搜索服务模型契约测试"""

    def test_search_index_model_fields(self):
        """测试搜索索引模型字段"""
        from app.models import SearchIndex

        assert SearchIndex.__tablename__ == "search_indices"
        assert hasattr(SearchIndex, "id")
        assert hasattr(SearchIndex, "item_type")
        assert hasattr(SearchIndex, "item_id")
        assert hasattr(SearchIndex, "title")
        assert hasattr(SearchIndex, "content")
        assert hasattr(SearchIndex, "keywords")
        assert hasattr(SearchIndex, "status")
        assert hasattr(SearchIndex, "created_at")
        assert hasattr(SearchIndex, "updated_at")

    def test_hot_search_model_fields(self):
        """测试热门搜索模型字段"""
        from app.models import HotSearch

        assert HotSearch.__tablename__ == "hot_searches"
        assert hasattr(HotSearch, "id")
        assert hasattr(HotSearch, "keyword")
        assert hasattr(HotSearch, "search_count")
        assert hasattr(HotSearch, "status")
        assert hasattr(HotSearch, "updated_at")


class TestSearchServiceResponseContract:
    """搜索服务响应格式契约测试"""

    def test_search_item_structure(self):
        """测试搜索项结构"""
        from app.services.search_service import SearchItem

        item = SearchItem(
            id=1,
            type="news",
            title="测试标题",
            description="测试描述",
            url="/news/1",
            score=0.9
        )

        assert item.id == 1
        assert item.type == "news"
        assert item.title == "测试标题"
        assert isinstance(item.score, float)

    def test_search_response_structure(self):
        """测试搜索响应结构"""
        expected_keys = {"items", "total", "query", "type"}

        response = {
            "items": [
                {
                    "id": 1,
                    "type": "news",
                    "title": "新闻标题",
                    "description": "新闻描述",
                    "url": "/news/1",
                    "score": 0.9
                }
            ],
            "total": 1,
            "query": "测试查询",
            "type": "news"
        }

        assert set(response.keys()) == expected_keys
        assert isinstance(response["items"], list)
        assert isinstance(response["total"], int)

    def test_suggestion_response_structure(self):
        """测试搜索建议响应结构"""
        suggestion = {
            "text": "法律咨询",
            "count": 1000
        }

        assert "text" in suggestion
        assert "count" in suggestion
        assert isinstance(suggestion["text"], str)
        assert isinstance(suggestion["count"], int)

    def test_hot_search_response_structure(self):
        """测试热门搜索响应结构"""
        hot_search = {
            "keyword": "离婚程序",
            "count": 15230
        }

        assert "keyword" in hot_search
        assert "count" in hot_search
        assert isinstance(hot_search["keyword"], str)
        assert isinstance(hot_search["count"], int)
