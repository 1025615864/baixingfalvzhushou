"""新闻主题服务测试 (news/topics.py)"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.news.topics import NewsTopicService
from app.models.news import News, NewsTopic, NewsTopicItem
from app.schemas.news import (
    NewsTopicResponse,
    NewsTopicDetailResponse,
    NewsListItem,
    NewsTopicCreate,
    NewsTopicUpdate,
)


class TestNewsTopicService:
    """测试新闻主题服务"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def mock_topic(self):
        """创建模拟新闻主题对象"""
        topic = MagicMock(spec=NewsTopic)
        topic.id = 1
        topic.title = "劳动法专题"
        topic.slug = "labor-law"
        topic.description = "劳动法相关新闻"
        topic.is_active = True
        topic.created_at = datetime.now(timezone.utc)
        topic.cover_image = None
        topic.auto_category = None
        topic.auto_keyword = None
        return topic

    @pytest.mark.asyncio
    async def test_list_topics(self, mock_db, mock_topic):
        """测试获取主题列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_topic]
        mock_db.execute.return_value = mock_result

        service = NewsTopicService()
        topics = await service.list_topics(mock_db, active_only=True)

        assert len(topics) == 1
        assert topics[0].id == 1
        assert topics[0].title == "劳动法专题"

    @pytest.mark.asyncio
    async def test_list_topics_inactive(self, mock_db, mock_topic):
        """测试获取主题列表（包含非活跃）"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_topic]
        mock_db.execute.return_value = mock_result

        service = NewsTopicService()
        topics = await service.list_topics(mock_db, active_only=False)

        assert len(topics) == 1

    @pytest.mark.asyncio
    async def test_list_topics_empty(self, mock_db):
        """测试获取空主题列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = NewsTopicService()
        topics = await service.list_topics(mock_db, active_only=True)

        assert len(topics) == 0

    @pytest.mark.asyncio
    async def test_get_topic(self, mock_db, mock_topic):
        """测试获取主题详情"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_topic
        mock_db.execute.return_value = mock_result

        service = NewsTopicService()
        topic = await service.get_topic(mock_db, topic_id=1)

        assert topic is not None
        assert topic.id == 1
        assert topic.title == "劳动法专题"

    @pytest.mark.asyncio
    async def test_get_topic_not_found(self, mock_db):
        """测试获取不存在的主题"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = NewsTopicService()
        topic = await service.get_topic(mock_db, topic_id=999)

        assert topic is None

    @pytest.mark.asyncio
    async def test_create_topic(self, mock_db):
        """测试创建主题"""
        mock_topic = MagicMock(spec=NewsTopic)
        mock_topic.id = 1
        mock_topic.title = "新专题"
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        service = NewsTopicService()
        data = {
            "title": "新专题",
            "description": "新专题描述",
        }

        topic = await service.create_topic(mock_db, data)

        assert topic is not None

    @pytest.mark.asyncio
    async def test_update_topic(self, mock_db, mock_topic):
        """测试更新主题"""
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        service = NewsTopicService()
        data = {"title": "更新后的专题名"}
        topic = await service.update_topic(mock_db, mock_topic, data)

        assert topic is not None
        assert topic.title == "更新后的专题名"

    @pytest.mark.asyncio
    async def test_delete_topic(self, mock_db):
        """测试删除主题"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(spec=NewsTopic)
        mock_db.execute.return_value = mock_result
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        service = NewsTopicService()
        await service.delete_topic(mock_db, topic_id=1)

    @pytest.mark.asyncio
    async def test_delete_topic_not_found(self, mock_db):
        """测试删除不存在的主题"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = NewsTopicService()
        await service.delete_topic(mock_db, topic_id=999)

    @pytest.mark.asyncio
    async def test_list_topic_items_brief(self, mock_db):
        """测试获取专题项简要列表"""
        mock_item = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_item]
        mock_db.execute.return_value = mock_result

        service = NewsTopicService()
        items = await service.list_topic_items_brief(mock_db, topic_id=1)

        assert len(items) == 1

    @pytest.mark.asyncio
    async def test_add_topic_item(self, mock_db):
        """测试添加专题项"""
        mock_item = MagicMock(spec=NewsTopicItem)
        mock_item.id = 1
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_db.execute.return_value = MagicMock(scalar=MagicMock(return_value=0))

        service = NewsTopicService()
        item = await service.add_topic_item(mock_db, topic_id=1, news_id=1)

        assert item is not None

    @pytest.mark.asyncio
    async def test_add_topic_items_bulk(self, mock_db):
        """测试批量添加专题项"""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        service = NewsTopicService()
        items = await service.add_topic_items_bulk(mock_db, topic_id=1, news_ids=[1, 2, 3])

        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_update_topic_item_position(self, mock_db):
        """测试更新专题项位置"""
        mock_item = MagicMock(spec=NewsTopicItem)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_item
        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None

        service = NewsTopicService()
        result = await service.update_topic_item_position(mock_db, topic_id=1, item_id=1, position=1)

        assert result is True

    @pytest.mark.asyncio
    async def test_update_topic_item_position_not_found(self, mock_db):
        """测试更新不存在的专题项位置"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = NewsTopicService()
        result = await service.update_topic_item_position(mock_db, topic_id=1, item_id=999, position=1)

        assert result is False

    @pytest.mark.asyncio
    async def test_remove_topic_item(self, mock_db):
        """测试移除专题项"""
        mock_item = MagicMock(spec=NewsTopicItem)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_item
        mock_db.execute.return_value = mock_result
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        service = NewsTopicService()
        result = await service.remove_topic_item(mock_db, topic_id=1, item_id=1)

        assert result is True

    @pytest.mark.asyncio
    async def test_remove_topic_item_not_found(self, mock_db):
        """测试移除不存在的专题项"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = NewsTopicService()
        result = await service.remove_topic_item(mock_db, topic_id=1, item_id=999)

        assert result is False

    @pytest.mark.asyncio
    async def test_remove_topic_items_bulk(self, mock_db):
        """测试批量移除专题项"""
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None

        service = NewsTopicService()
        count = await service.remove_topic_items_bulk(mock_db, topic_id=1, item_ids=[1, 2, 3])

        assert count == 3

    @pytest.mark.asyncio
    async def test_reindex_topic_items(self, mock_db):
        """测试重新索引专题项"""
        mock_item = MagicMock(spec=NewsTopicItem)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_item]
        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None

        service = NewsTopicService()
        count = await service.reindex_topic_items(mock_db, topic_id=1)

        assert count == 1

    @pytest.mark.asyncio
    async def test_reorder_topic_items(self, mock_db):
        """测试重新排序专题项"""
        mock_item = MagicMock(spec=NewsTopicItem)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_item
        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None

        service = NewsTopicService()
        count = await service.reorder_topic_items(mock_db, topic_id=1, item_ids=[1, 2, 3])

        assert count == 3
