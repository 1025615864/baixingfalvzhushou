import pytest
from app.models import News, NewsCategory, NewsTag, UserNewsInteraction


class TestHealthEndpoints:

    @pytest.mark.asyncio
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "news-service"

    @pytest.mark.asyncio
    async def test_readiness(self, client):
        response = await client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    @pytest.mark.asyncio
    async def test_liveness(self, client):
        response = await client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"


class TestNewsList:

    @pytest.mark.asyncio
    async def test_list_news_default(self, client, db_session):
        category = NewsCategory(name="法律资讯", code="legal", description="法律相关资讯", sort_order=1)
        db_session.add(category)
        await db_session.commit()
        news = News(
            title="测试新闻标题",
            content="这是测试新闻的完整内容",
            summary="测试摘要",
            category_id=category.id,
            status="published",
        )
        db_session.add(news)
        await db_session.commit()

        response = await client.get("/api/v1/news/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_news_with_pagination(self, client, db_session):
        category = NewsCategory(name="分页测试", code="page_test", sort_order=2)
        db_session.add(category)
        await db_session.commit()
        for i in range(5):
            news = News(
                title=f"分页新闻{i}",
                content=f"内容{i}",
                summary=f"摘要{i}",
                category_id=category.id,
                status="published",
            )
            db_session.add(news)
        await db_session.commit()

        response = await client.get("/api/v1/news/?page=1&page_size=3")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert len(data["items"]) <= 3

    @pytest.mark.asyncio
    async def test_list_news_with_category_filter(self, client, db_session):
        category = NewsCategory(name="分类筛选", code="cat_filter", sort_order=3)
        db_session.add(category)
        await db_session.commit()

        response = await client.get(f"/api/v1/news/?category_id={category.id}")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        for item in data["items"]:
            assert item["category_id"] == category.id

    @pytest.mark.asyncio
    async def test_list_news_with_search(self, client, db_session):
        category = NewsCategory(name="搜索测试", code="search_test", sort_order=4)
        db_session.add(category)
        await db_session.commit()
        news = News(
            title="民法典最新解读",
            content="民法典的详细解读内容",
            summary="民法典解读摘要",
            category_id=category.id,
            status="published",
        )
        db_session.add(news)
        await db_session.commit()

        response = await client.get("/api/v1/news/?q=民法典")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_list_news_sort_by_hot(self, client, db_session):
        category = NewsCategory(name="热度排序", code="hot_sort", sort_order=5)
        db_session.add(category)
        await db_session.commit()
        news_a = News(title="冷门新闻", content="内容", summary="摘要", category_id=category.id, view_count=10, status="published")
        news_b = News(title="热门新闻", content="内容", summary="摘要", category_id=category.id, view_count=1000, status="published")
        db_session.add_all([news_a, news_b])
        await db_session.commit()

        response = await client.get("/api/v1/news/?sort_by=hot")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestNewsDetail:

    @pytest.mark.asyncio
    async def test_get_news_detail(self, client, db_session):
        category = NewsCategory(name="详情测试", code="detail_test", sort_order=6)
        db_session.add(category)
        await db_session.commit()
        news = News(
            title="详情测试新闻",
            content="这是新闻的完整内容",
            summary="详情摘要",
            category_id=category.id,
            source="测试来源",
            author="测试作者",
            status="published",
        )
        db_session.add(news)
        await db_session.commit()

        response = await client.get(f"/api/v1/news/{news.id}")
        assert response.status_code == 200
        data = response.json()
        assert "news" in data
        assert data["news"]["title"] == "详情测试新闻"
        assert data["news"]["content"] == "这是新闻的完整内容"
        assert data["news"]["source"] == "测试来源"
        assert data["news"]["author"] == "测试作者"
        assert "is_bookmarked" in data

    @pytest.mark.asyncio
    async def test_get_news_detail_not_found(self, client):
        response = await client.get("/api/v1/news/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "新闻不存在"

    @pytest.mark.asyncio
    async def test_get_news_detail_with_user_bookmark(self, client, db_session):
        category = NewsCategory(name="收藏详情", code="bookmark_detail", sort_order=7)
        db_session.add(category)
        await db_session.commit()
        news = News(
            title="收藏测试新闻",
            content="内容",
            summary="摘要",
            category_id=category.id,
            status="published",
        )
        db_session.add(news)
        await db_session.commit()
        interaction = UserNewsInteraction(user_id=1, news_id=news.id, is_bookmarked=True)
        db_session.add(interaction)
        await db_session.commit()

        response = await client.get(f"/api/v1/news/{news.id}?user_id=1")
        assert response.status_code == 200
        data = response.json()
        assert data["is_bookmarked"] is True


class TestNewsBookmark:

    @pytest.mark.asyncio
    async def test_bookmark_news(self, client, db_session):
        category = NewsCategory(name="收藏测试", code="bookmark_test", sort_order=8)
        db_session.add(category)
        await db_session.commit()
        news = News(
            title="收藏新闻",
            content="内容",
            summary="摘要",
            category_id=category.id,
            status="published",
        )
        db_session.add(news)
        await db_session.commit()

        response = await client.post(f"/api/v1/news/{news.id}/bookmark?user_id=1")
        assert response.status_code == 200
        assert response.json()["message"] == "收藏成功"

    @pytest.mark.asyncio
    async def test_unbookmark_news(self, client, db_session):
        category = NewsCategory(name="取消收藏", code="unbookmark", sort_order=9)
        db_session.add(category)
        await db_session.commit()
        news = News(
            title="取消收藏新闻",
            content="内容",
            summary="摘要",
            category_id=category.id,
            status="published",
        )
        db_session.add(news)
        await db_session.commit()

        await client.post(f"/api/v1/news/{news.id}/bookmark?user_id=1")
        response = await client.delete(f"/api/v1/news/{news.id}/bookmark?user_id=1")
        assert response.status_code == 200
        assert response.json()["message"] == "取消收藏成功"

    @pytest.mark.asyncio
    async def test_get_user_bookmarks(self, client, db_session):
        response = await client.get("/api/v1/news/user/bookmarks?user_id=1")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestNewsSearch:

    @pytest.mark.asyncio
    async def test_search_news(self, client, db_session):
        category = NewsCategory(name="搜索", code="search", sort_order=10)
        db_session.add(category)
        await db_session.commit()
        news = News(
            title="劳动法修订案通过",
            content="劳动法修订案详细内容",
            summary="劳动法修订摘要",
            category_id=category.id,
            status="published",
        )
        db_session.add(news)
        await db_session.commit()

        response = await client.get("/api/v1/news/search?q=劳动法")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_news_missing_query(self, client):
        response = await client.get("/api/v1/news/search")
        assert response.status_code == 422


class TestNewsCategories:

    @pytest.mark.asyncio
    async def test_list_categories(self, client, db_session):
        category = NewsCategory(name="分类列表测试", code="cat_list", description="测试分类", sort_order=11)
        db_session.add(category)
        await db_session.commit()

        response = await client.get("/api/v1/news/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] is not None
        assert data[0]["code"] is not None
