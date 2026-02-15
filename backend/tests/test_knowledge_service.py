"""知识库服务测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.knowledge import KnowledgeService, knowledge_service
from app.models.knowledge import LegalKnowledge, KnowledgeType
from app.schemas.knowledge import (
    LegalKnowledgeCreate,
    LegalKnowledgeUpdate,
    KnowledgeStats,
)


class TestKnowledgeService:
    """知识库服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self):
        """创建知识库服务实例"""
        return KnowledgeService()

    @pytest.fixture
    def mock_knowledge(self):
        """创建模拟知识条目"""
        knowledge = MagicMock(spec=LegalKnowledge)
        knowledge.id = 1
        knowledge.title = "民法典第101条"
        knowledge.content = "自然人享有隐私权..."
        knowledge.knowledge_type = "law"
        knowledge.category = "民法典"
        knowledge.keywords = "隐私权,自然人"
        knowledge.is_active = True
        knowledge.is_vectorized = True
        return knowledge

    def test_compute_source_hash(self, service):
        """测试计算源哈希"""
        hash1 = service._compute_source_hash(
            knowledge_type="law",
            title="民法典第101条",
            article_number="101",
            content="自然人享有隐私权...",
            source_url="https://example.com/law/101",
            source_version="2024",
        )

        hash2 = service._compute_source_hash(
            knowledge_type="law",
            title="民法典第101条",
            article_number="101",
            content="自然人享有隐私权...",
            source_url="https://example.com/law/101",
            source_version="2024",
        )

        hash3 = service._compute_source_hash(
            knowledge_type="law",
            title="民法典第102条",
            article_number="102",
            content="自然人享有隐私权...",
            source_url="https://example.com/law/101",
            source_version="2024",
        )

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64

    @pytest.mark.asyncio
    async def test_get_knowledge_found(self, service, mock_db, mock_knowledge):
        """测试获取知识（存在）"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_knowledge
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_knowledge(mock_db, knowledge_id=1)

        assert result is not None
        assert result.id == 1
        assert result.title == "民法典第101条"

    @pytest.mark.asyncio
    async def test_get_knowledge_not_found(self, service, mock_db):
        """测试获取知识（不存在）"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_knowledge(mock_db, knowledge_id=999)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_knowledge_success(self, service, mock_db, mock_knowledge):
        """测试删除知识成功"""
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = mock_knowledge

        mock_delete_result = MagicMock()
        mock_delete_result.rowcount = 1

        mock_db.execute = AsyncMock(side_effect=[mock_get_result, mock_delete_result])
        mock_db.delete = AsyncMock()

        result = await service.delete_knowledge(mock_db, knowledge_id=1)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_knowledge)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_knowledge_not_found(self, service, mock_db):
        """测试删除不存在的知识"""
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(return_value=mock_get_result)

        result = await service.delete_knowledge(mock_db, knowledge_id=999)

        assert result is False

    @pytest.mark.asyncio
    async def test_batch_delete_knowledge(self, service, mock_db):
        """测试批量删除知识"""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 2
        mock_db.execute = AsyncMock(return_value=mock_cursor)

        deleted, failed = await service.batch_delete_knowledge(mock_db, ids=[1, 2, 3])

        assert deleted == 2
        assert failed == 1

    @pytest.mark.asyncio
    async def test_get_categories(self, service, mock_db):
        """测试获取所有分类"""
        mock_result = MagicMock()
        mock_result.all.return_value = [("民法典",), ("刑法",), ("商法",)]
        mock_db.execute = AsyncMock(return_value=mock_result)

        categories = await service.get_categories(mock_db)

        assert len(categories) == 3
        assert "民法典" in categories
        assert "刑法" in categories
        assert "商法" in categories

    def test_service_singleton(self):
        """测试服务单例"""
        service1 = knowledge_service
        service2 = knowledge_service
        assert service1 is service2

    def test_get_knowledge_service(self):
        """测试获取服务实例"""
        from app.services.knowledge import get_knowledge_service

        service = get_knowledge_service()
        assert isinstance(service, KnowledgeService)

        service2 = get_knowledge_service()
        assert service is service2
