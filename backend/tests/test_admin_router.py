"""测试管理后台路由"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


class TestAdminRouter:
    """测试管理后台路由"""

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计数据"""
        from app.routers.admin import get_stats
        from app.models.user import User
        
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.scalar.return_value = 100
        mock_news = MagicMock()
        mock_news.scalar.return_value = 50
        mock_post = MagicMock()
        mock_post.scalar.return_value = 200
        mock_comment = MagicMock()
        mock_comment.scalar.return_value = 300
        mock_consultation = MagicMock()
        mock_consultation.scalar.return_value = 150
        mock_firm = MagicMock()
        mock_firm.scalar.return_value = 25
        
        mock_db.execute.side_effect = [
            mock_user,
            mock_news,
            mock_post,
            mock_comment,
            mock_consultation,
            mock_firm
        ]
        
        mock_user_obj = User(id=1, username="admin")
        
        result = await get_stats(mock_user_obj, mock_db)
        
        assert result["users"] == 100
        assert result["news"] == 50
        assert result["posts"] == 200
        assert result["comments"] == 300
        assert result["consultations"] == 150
        assert result["lawfirms"] == 25

    def test_generate_csv(self):
        """测试生成CSV内容"""
        from app.routers.admin import generate_csv
        from datetime import datetime
        
        data = [
            {"id": 1, "name": "Test", "created_at": datetime(2026, 1, 26)},
            {"id": 2, "name": "Test2", "created_at": datetime(2026, 1, 27)},
        ]
        fieldnames = ["id", "name", "created_at"]
        
        result = generate_csv(data, fieldnames)
        
        assert "id,name,created_at" in result.getvalue()
        assert "1,Test" in result.getvalue()
        assert "2,Test2" in result.getvalue()

    @pytest.mark.asyncio
    async def test_export_users(self):
        """测试导出用户数据"""
        from app.routers.admin import export_users
        from app.models.user import User
        
        mock_db = AsyncMock()
        mock_user1 = User(id=1, username="user1", email="user1@test.com", is_active=True)
        mock_user2 = User(id=2, username="user2", email="user2@test.com", is_active=False)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user1, mock_user2]
        
        # First call returns users, second call returns empty
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = []
        
        mock_db.execute.side_effect = [mock_result, mock_result2]
        
        mock_user = User(id=1, username="admin")
        
        result = await export_users(mock_user, mock_db)
        
        assert result.media_type == "text/csv; charset=utf-8-sig"
        assert "attachment; filename=" in result.headers["Content-Disposition"]
        
        # Test streaming
        content = ""
        async for chunk in result.body_iterator:
            content += chunk
        
        assert "id,username,email" in content
        assert "user1" in content
        assert "user2" in content

    @pytest.mark.asyncio
    async def test_export_posts(self):
        """测试导出帖子数据"""
        from app.routers.admin import export_posts
        from app.models.user import User
        from app.models.forum import Post
        
        mock_db = AsyncMock()
        mock_post = Post(id=1, title="Test Post", category="test", view_count=100, like_count=50)
        
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_post, "user1")]
        mock_result2 = MagicMock()
        mock_result2.all.return_value = []
        
        mock_db.execute.side_effect = [mock_result, mock_result2]
        
        mock_user = User(id=1, username="admin")
        
        result = await export_posts(mock_user, mock_db)
        
        assert result.media_type == "text/csv; charset=utf-8-sig"
        
        # Test streaming
        content = ""
        async for chunk in result.body_iterator:
            content += chunk
        
        assert "id,title,author" in content
        assert "Test Post" in content

    @pytest.mark.asyncio
    async def test_export_news(self):
        """测试导出新闻数据"""
        from app.routers.admin import export_news
        from app.models.user import User
        from app.models.news import News
        
        mock_db = AsyncMock()
        mock_news = News(id=1, title="Test News", category="news", view_count=100, is_published=True)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_news]
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = []
        
        mock_db.execute.side_effect = [mock_result, mock_result2]
        
        mock_user = User(id=1, username="admin")
        
        result = await export_news(mock_user, mock_db)
        
        assert result.media_type == "text/csv; charset=utf-8-sig"
        
        # Test streaming
        content = ""
        async for chunk in result.body_iterator:
            content += chunk
        
        assert "id,title,category" in content
        assert "Test News" in content

    @pytest.mark.asyncio
    async def test_export_lawfirms(self):
        """测试导出律所数据"""
        from app.routers.admin import export_lawfirms
        from app.models.user import User
        from app.models.lawfirm import LawFirm
        
        mock_db = AsyncMock()
        mock_firm = LawFirm(id=1, name="Test Firm", city="Beijing", rating=4.5, is_verified=True, is_active=True)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_firm]
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = []
        
        mock_db.execute.side_effect = [mock_result, mock_result2]
        
        mock_user = User(id=1, username="admin")
        
        result = await export_lawfirms(mock_user, mock_db)
        
        assert result.media_type == "text/csv; charset=utf-8-sig"
        
        # Test streaming
        content = ""
        async for chunk in result.body_iterator:
            content += chunk
        
        assert "id,name,city" in content
        assert "Test Firm" in content

    @pytest.mark.asyncio
    async def test_export_knowledge(self):
        """测试导出知识库数据"""
        from app.routers.admin import export_knowledge
        from app.models.user import User
        from app.models.knowledge import LegalKnowledge
        
        mock_db = AsyncMock()
        mock_knowledge = LegalKnowledge(
            id=1,
            knowledge_type="law",
            title="Test Knowledge",
            article_number="123",
            category="civil",
            content="Test content",
            keywords="test",
            source="test",
            is_active=True,
            is_vectorized=True
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_knowledge]
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = []
        
        mock_db.execute.side_effect = [mock_result, mock_result2]
        
        mock_user = User(id=1, username="admin")
        
        result = await export_knowledge(mock_user, mock_db)
        
        assert result.media_type == "text/csv; charset=utf-8-sig"
        
        # Test streaming
        content = ""
        async for chunk in result.body_iterator:
            content += chunk
        
        assert "id,knowledge_type,title" in content
        assert "Test Knowledge" in content

    @pytest.mark.asyncio
    async def test_export_consultations(self):
        """测试导出咨询记录"""
        from app.routers.admin import export_consultations
        from app.models.user import User
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(1, "session1", "Test Consultation", None, None, "user1", 5)]
        mock_result2 = MagicMock()
        mock_result2.all.return_value = []
        
        mock_db.execute.side_effect = [mock_result, mock_result2]
        
        mock_user = User(id=1, username="admin")
        
        result = await export_consultations(mock_user, mock_db)
        
        assert result.media_type == "text/csv; charset=utf-8-sig"
        
        # Test streaming
        content = ""
        async for chunk in result.body_iterator:
            content += chunk
        
        assert "id,session_id,user" in content
        assert "Test Consultation" in content
