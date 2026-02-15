"""FAQ服务测试"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.faq import FAQService, faq_service
from app.models.faq import FAQ


class TestFAQService:
    """FAQ服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def mock_faq(self):
        """创建模拟FAQ"""
        faq = MagicMock(spec=FAQ)
        faq.id = 1
        faq.question = "如何申请劳动仲裁？"
        faq.answer = "准备好相关材料，向劳动仲裁委员会申请..."
        faq.category = "劳动纠纷"
        faq.tags = json.dumps(["劳动", "仲裁"])
        faq.priority = 10
        faq.is_active = True
        faq.view_count = 100
        return faq

    @pytest.mark.asyncio
    async def test_search_faqs_basic(self, mock_db, mock_faq):
        """测试搜索FAQ（基础）"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_faq]
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

        faqs, total = await FAQService.search_faqs(mock_db)

        assert total == 1
        assert len(faqs) == 1
        assert faqs[0].id == 1

    @pytest.mark.asyncio
    async def test_search_faqs_with_keyword(self, mock_db):
        """测试关键词搜索FAQ"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

        faqs, total = await FAQService.search_faqs(mock_db, keyword="劳动仲裁")

        assert total == 0

    @pytest.mark.asyncio
    async def test_search_faqs_with_category(self, mock_db):
        """测试按分类筛选FAQ"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

        faqs, total = await FAQService.search_faqs(mock_db, category="劳动纠纷")

        assert total == 0

    @pytest.mark.asyncio
    async def test_search_faqs_with_tags(self, mock_db):
        """测试按标签筛选FAQ"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

        faqs, total = await FAQService.search_faqs(mock_db, tags=["劳动", "仲裁"])

        assert total == 0

    @pytest.mark.asyncio
    async def test_search_faqs_inactive(self, mock_db):
        """测试搜索包含非激活的FAQ"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

        faqs, total = await FAQService.search_faqs(mock_db, is_active=None)

        assert total == 0

    @pytest.mark.asyncio
    async def test_get_faq_by_id_found(self, mock_db, mock_faq):
        """测试获取FAQ（存在）"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_faq
        mock_db.execute = AsyncMock(return_value=mock_result)

        faq = await FAQService.get_faq_by_id(mock_db, faq_id=1)

        assert faq is not None
        assert faq.id == 1
        assert faq.question == "如何申请劳动仲裁？"

    @pytest.mark.asyncio
    async def test_get_faq_by_id_not_found(self, mock_db):
        """测试获取FAQ（不存在）"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        faq = await FAQService.get_faq_by_id(mock_db, faq_id=999)

        assert faq is None

    @pytest.mark.asyncio
    async def test_get_faq_categories(self, mock_db):
        """测试获取FAQ分类"""
        mock_result = MagicMock()
        mock_result.all.return_value = [("劳动纠纷",), ("婚姻家庭",), ("房产纠纷",)]
        mock_db.execute = AsyncMock(return_value=mock_result)

        categories = await FAQService.get_faq_categories(mock_db)

        assert len(categories) == 3
        assert "劳动纠纷" in categories
        assert "婚姻家庭" in categories
        assert "房产纠纷" in categories

    @pytest.mark.asyncio
    async def test_get_popular_faqs(self, mock_db, mock_faq):
        """测试获取热门FAQ"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_faq]
        mock_db.execute = AsyncMock(return_value=mock_result)

        faqs = await FAQService.get_popular_faqs(mock_db, limit=10)

        assert len(faqs) == 1

    @pytest.mark.asyncio
    async def test_get_popular_faqs_with_category(self, mock_db):
        """测试按分类获取热门FAQ"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        faqs = await FAQService.get_popular_faqs(mock_db, limit=10, category="劳动纠纷")

        assert len(faqs) == 0

    @pytest.mark.asyncio
    async def test_increment_view_count_success(self, mock_db, mock_faq):
        """测试增加浏览量成功"""
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = mock_faq
        mock_db.execute = AsyncMock(return_value=mock_get_result)

        result = await FAQService.increment_view_count(mock_db, faq_id=1)

        assert result is True
        assert mock_faq.view_count == 101
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_view_count_not_found(self, mock_db):
        """测试增加不存在的FAQ浏览量"""
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_get_result)

        result = await FAQService.increment_view_count(mock_db, faq_id=999)

        assert result is False

    @pytest.mark.asyncio
    async def test_create_faq(self, mock_db, mock_faq):
        """测试创建FAQ"""
        mock_db.add = MagicMock()
        mock_db.refresh = AsyncMock()

        faq = await FAQService.create_faq(
            mock_db,
            question="如何申请劳动仲裁？",
            answer="准备好相关材料，向劳动仲裁委员会申请...",
            category="劳动纠纷",
            tags=["劳动", "仲裁"],
            priority=10,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert faq.question == "如何申请劳动仲裁？"

    @pytest.mark.asyncio
    async def test_update_faq_success(self, mock_db, mock_faq):
        """测试更新FAQ成功"""
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = mock_faq
        mock_db.execute = AsyncMock(return_value=mock_get_result)

        updated_faq = await FAQService.update_faq(
            mock_db,
            faq_id=1,
            question="更新后的问题",
        )

        assert updated_faq is not None
        assert updated_faq.question == "更新后的问题"

    @pytest.mark.asyncio
    async def test_update_faq_not_found(self, mock_db):
        """测试更新不存在的FAQ"""
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_get_result)

        updated_faq = await FAQService.update_faq(
            mock_db,
            faq_id=999,
            question="更新后的问题",
        )

        assert updated_faq is None

    @pytest.mark.asyncio
    async def test_delete_faq_success(self, mock_db, mock_faq):
        """测试删除FAQ成功"""
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = mock_faq
        mock_db.execute = AsyncMock(return_value=mock_get_result)

        result = await FAQService.delete_faq(mock_db, faq_id=1)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_faq)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_faq_not_found(self, mock_db):
        """测试删除不存在的FAQ"""
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_get_result)

        result = await FAQService.delete_faq(mock_db, faq_id=999)

        assert result is False

    def test_service_singleton(self):
        """测试服务单例"""
        service1 = faq_service
        service2 = faq_service
        assert service1 is service2
