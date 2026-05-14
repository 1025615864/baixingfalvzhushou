"""新闻服务契约测试"""
import pytest
from httpx import AsyncClient


class TestNewsServiceContract:
    """新闻服务契约测试"""

    @pytest.mark.asyncio
    async def test_get_news_list(self, client: AsyncClient):
        """测试获取新闻列表"""
        response = await client.get(
            "/api/v1/news/",
            params={"page": 1, "page_size": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_get_news_list_with_category(self, client: AsyncClient):
        """测试按分类获取新闻列表"""
        response = await client.get(
            "/api/v1/news/",
            params={"category_id": 1, "page": 1, "page_size": 10}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_news_list_with_tag(self, client: AsyncClient):
        """测试按标签获取新闻列表"""
        response = await client.get(
            "/api/v1/news/",
            params={"tag_id": 1, "page": 1, "page_size": 10}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_search_news(self, client: AsyncClient):
        """测试搜索新闻"""
        response = await client.get(
            "/api/v1/news/search",
            params={"q": "法律", "page": 1, "page_size": 10}
        )
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_get_news_detail(self, client: AsyncClient):
        """测试获取新闻详情"""
        response = await client.get("/api/v1/news/1")
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "news" in data
            assert "id" in data["news"]
            assert "title" in data["news"]
            assert "content" in data["news"]

    @pytest.mark.asyncio
    async def test_get_news_categories(self, client: AsyncClient):
        """测试获取新闻分类列表"""
        response = await client.get("/api/v1/news/categories")
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            if len(data) > 0:
                assert "id" in data[0]
                assert "name" in data[0]
                assert "code" in data[0]

    @pytest.mark.asyncio
    async def test_get_news_tags(self, client: AsyncClient):
        """测试获取新闻标签列表"""
        response = await client.get("/api/v1/news/tags")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_bookmark_news(self, client: AsyncClient):
        """测试收藏新闻"""
        response = await client.post(
            "/api/v1/news/1/bookmark",
            params={"user_id": 1}
        )
        assert response.status_code in [200, 401, 404]

    @pytest.mark.asyncio
    async def test_unbookmark_news(self, client: AsyncClient):
        """测试取消收藏新闻"""
        response = await client.delete(
            "/api/v1/news/1/bookmark",
            params={"user_id": 1}
        )
        assert response.status_code in [200, 401, 404]

    @pytest.mark.asyncio
    async def test_get_user_bookmarks(self, client: AsyncClient):
        """测试获取用户收藏"""
        response = await client.get(
            "/api/v1/news/user/bookmarks",
            params={"user_id": 1, "page": 1, "page_size": 10}
        )
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data


class TestNewsServiceModelsContract:
    """新闻服务模型契约测试"""

    def test_news_model_fields(self):
        """测试新闻模型字段"""
        from app.models import News

        assert News.__tablename__ == "news"
        assert hasattr(News, "id")
        assert hasattr(News, "title")
        assert hasattr(News, "content")
        assert hasattr(News, "summary")
        assert hasattr(News, "category_id")
        assert hasattr(News, "author")
        assert hasattr(News, "view_count")
        assert hasattr(News, "like_count")
        assert hasattr(News, "published_at")

    def test_news_category_model_fields(self):
        """测试新闻分类模型字段"""
        from app.models import NewsCategory

        assert NewsCategory.__tablename__ == "news_categories"
        assert hasattr(NewsCategory, "id")
        assert hasattr(NewsCategory, "name")
        assert hasattr(NewsCategory, "code")
        assert hasattr(NewsCategory, "description")
        assert hasattr(NewsCategory, "sort_order")

    def test_news_tag_model_fields(self):
        """测试新闻标签模型字段"""
        from app.models import NewsTag

        assert NewsTag.__tablename__ == "news_tags"
        assert hasattr(NewsTag, "id")
        assert hasattr(NewsTag, "name")
        assert hasattr(NewsTag, "slug")
        assert hasattr(NewsTag, "news_count")

    def test_user_news_interaction_model_fields(self):
        """测试用户新闻互动模型字段"""
        from app.models import UserNewsInteraction

        assert UserNewsInteraction.__tablename__ == "user_news_interactions"
        assert hasattr(UserNewsInteraction, "id")
        assert hasattr(UserNewsInteraction, "user_id")
        assert hasattr(UserNewsInteraction, "news_id")
        assert hasattr(UserNewsInteraction, "is_bookmarked")
        assert hasattr(UserNewsInteraction, "is_liked")
        assert hasattr(UserNewsInteraction, "interacted_at")


class TestNewsServiceResponseContract:
    """新闻服务响应格式契约测试"""

    def test_news_out_schema(self):
        """测试新闻输出响应格式"""
        from datetime import datetime, timezone
        from app.routers.news import NewsOut

        news = NewsOut(
            id=1,
            title="测试新闻",
            summary="测试摘要",
            category_id=1,
            cover_image="https://example.com/image.jpg",
            view_count=100,
            like_count=10,
            share_count=5,
            published_at=datetime.now(timezone.utc)
        )

        assert news.id == 1
        assert news.title == "测试新闻"
        assert isinstance(news.view_count, int)
        assert isinstance(news.like_count, int)

    def test_news_list_response_schema(self):
        """测试新闻列表响应格式"""
        from app.routers.news import NewsListResponse, NewsOut

        response = NewsListResponse(
            items=[
                NewsOut(
                    id=1,
                    title="新闻1",
                    summary="摘要1",
                    category_id=1,
                    view_count=0,
                    like_count=0,
                    share_count=0
                )
            ],
            total=1,
            page=1,
            page_size=10
        )

        assert len(response.items) == 1
        assert response.total == 1
        assert response.page == 1
        assert response.page_size == 10
