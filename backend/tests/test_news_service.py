"""新闻服务测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.news import NewsService, news_service


class TestNewsServiceHelpers:
    """新闻服务辅助方法测试类"""

    def test_escape_like(self):
        """测试Like转义"""
        service = NewsService()
        
        assert service._escape_like("test") == "test"
        assert service._escape_like("te_st") == "te\\_st"
        assert service._escape_like("te%st") == "te\\%st"
        assert service._escape_like("\\") == "\\\\"

    def test_news_snapshot(self):
        """测试新闻快照"""
        service = NewsService()
        
        mock_news = MagicMock()
        mock_news.id = 1
        mock_news.title = "测试标题"
        mock_news.summary = "测试摘要"
        mock_news.content = "测试内容"
        mock_news.cover_image = "http://example.com/image.jpg"
        mock_news.category = "tech"
        mock_news.source = "测试来源"
        mock_news.source_url = "http://example.com"
        mock_news.source_site = "example.com"
        mock_news.author = "张三"
        mock_news.is_top = True
        mock_news.is_published = True
        mock_news.review_status = "approved"
        mock_news.review_reason = None
        mock_news.reviewed_at = datetime.now(timezone.utc)
        mock_news.published_at = datetime.now(timezone.utc)
        mock_news.scheduled_publish_at = None
        mock_news.scheduled_unpublish_at = None
        mock_news.created_at = datetime.now(timezone.utc)
        mock_news.updated_at = datetime.now(timezone.utc)

        snapshot = service._news_snapshot(mock_news)

        assert snapshot["id"] == 1
        assert snapshot["title"] == "测试标题"
        assert snapshot["is_top"] is True
        assert snapshot["review_status"] == "approved"


class TestNewsServiceCRUD:
    """新闻服务CRUD测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self):
        """创建新闻服务实例"""
        return NewsService()

    @pytest.mark.asyncio
    async def test_create_news(self, mock_db, service):
        """测试创建新闻"""
        from app.schemas.news import NewsCreate
        
        mock_news = MagicMock()
        mock_news.id = 1
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock(return_value=mock_news)

        with patch.object(service, '_snapshot_json', return_value='{}'):
            # 模拟 News 模型创建
            with patch('app.services.news.core.News') as MockNews:
                mock_news_instance = MagicMock()
                mock_news_instance.id = 1
                MockNews.return_value = mock_news_instance
                
                news_data = NewsCreate(
                    title="测试新闻",
                    content="测试内容",
                    category="tech",
                    source="测试来源"
                )

                result = await service.create(mock_db, news_data=news_data, admin_user_id=1)

                assert result is not None

    @pytest.mark.asyncio
    async def test_get_news_by_id(self, mock_db, service):
        """测试根据ID获取新闻"""
        mock_news = MagicMock()
        mock_news.id = 1
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_news
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_by_id(mock_db, news_id=1)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_news_by_id_not_found(self, mock_db, service):
        """测试根据ID获取新闻（不存在）"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_by_id(mock_db, news_id=999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_news_list(self, mock_db, service):
        """测试获取新闻列表"""
        mock_news = MagicMock()
        mock_news.id = 1
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_news]
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count])

        news_list, total = await service.get_list(mock_db, page=1, page_size=10)

        assert len(news_list) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_update_news(self, mock_db, service):
        """测试更新新闻"""
        from app.schemas.news import NewsUpdate
        
        mock_news = MagicMock()
        mock_news.versions_count = 1
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.flush = AsyncMock()

        update_data = NewsUpdate(title="新标题")
        
        with patch.object(service, '_snapshot_json', return_value='{}'):
            with patch('app.services.news.core.NewsVersion'):
                result = await service.update(mock_db, mock_news, news_data=update_data, admin_user_id=1)

        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_news(self, mock_db, service):
        """测试删除新闻"""
        mock_news = MagicMock()
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.delete(mock_db, mock_news)

        assert result is None  # delete returns None


class TestNewsPublishing:
    """新闻发布测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self):
        """创建新闻服务实例"""
        return NewsService()

    @pytest.mark.asyncio
    async def test_publish_news(self, mock_db, service):
        """测试发布新闻 - 通过update方法实现"""
        from app.schemas.news import NewsUpdate
        
        mock_news = MagicMock()
        mock_news.is_published = False
        mock_news.published_at = None
        mock_news.versions_count = 1
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.flush = AsyncMock()

        with patch.object(service, '_snapshot_json', return_value='{}'):
            # 使用update方法修改is_published字段
            update_data = NewsUpdate(is_published=True)
            result = await service.update(mock_db, mock_news, news_data=update_data, admin_user_id=1)

        assert result is not None

    @pytest.mark.asyncio
    async def test_publish_news_already_published(self, mock_db, service):
        """测试发布新闻（已发布）"""
        from app.schemas.news import NewsUpdate
        
        mock_news = MagicMock()
        mock_news.is_published = True
        mock_news.versions_count = 1
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.flush = AsyncMock()

        with patch.object(service, '_snapshot_json', return_value='{}'):
            update_data = NewsUpdate(is_published=True)
            result = await service.update(mock_db, mock_news, news_data=update_data, admin_user_id=1)

        assert result is not None

    @pytest.mark.asyncio
    async def test_unpublish_news(self, mock_db, service):
        """测试取消发布新闻 - 通过update方法实现"""
        from app.schemas.news import NewsUpdate
        
        mock_news = MagicMock()
        mock_news.is_published = True
        mock_news.versions_count = 1
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.flush = AsyncMock()

        with patch.object(service, '_snapshot_json', return_value='{}'):
            update_data = NewsUpdate(is_published=False)
            result = await service.update(mock_db, mock_news, news_data=update_data, admin_user_id=1)

        assert result is not None

    @pytest.mark.asyncio
    async def test_set_top_news(self, mock_db, service):
        """测试设置置顶新闻 - 通过update方法实现"""
        from app.schemas.news import NewsUpdate
        
        mock_news = MagicMock()
        mock_news.is_top = False
        mock_news.versions_count = 1
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.flush = AsyncMock()

        with patch.object(service, '_snapshot_json', return_value='{}'):
            update_data = NewsUpdate(is_top=True)
            result = await service.update(mock_db, mock_news, news_data=update_data, admin_user_id=1)

        assert result is not None
        assert mock_news.is_top is True


class TestNewsCache:
    """新闻缓存测试类"""

    def test_prune_cache(self):
        """测试缓存修剪"""
        import time
        
        cache = {
            "key1": (time.time() - 10, [1, 2]),
            "key2": (time.time() - 100, [3, 4]),
            "key3": (time.time() - 200, [5, 6])
        }
        now_ts = time.time()
        
        service = NewsService()
        original_len = len(cache)
        service._prune_cache(cache, ttl_seconds=60, now_ts=now_ts, max_size=10)

        # 缓存修剪应删除过期项，但保留在ttl内的项
        # key1是10秒前，在60秒ttl内，应该保留
        # key2和key3都超过60秒ttl，应该被删除
        assert "key1" in cache
        # 由于max_size=10大于当前缓存大小，不会触发按大小修剪


class TestNewsStatistics:
    """新闻统计测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self):
        """创建新闻服务实例"""
        return NewsService()

    @pytest.mark.asyncio
    async def test_increment_view_count(self, mock_db, service):
        """测试增加浏览量"""
        mock_news = MagicMock()
        mock_news.view_count = 100
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        await service.increment_view(mock_db, mock_news)

        assert mock_news.view_count == 101

    @pytest.mark.asyncio
    async def test_get_hot_news(self, mock_db, service):
        """测试获取热门新闻"""
        mock_news = MagicMock()
        mock_news.id = 1
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_news]
        mock_db.execute = AsyncMock(return_value=mock_result)

        hot_news = await service.get_hot_news(mock_db, days=7, limit=10)

        assert len(hot_news) == 1
