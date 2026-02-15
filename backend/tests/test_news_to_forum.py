"""Tests for News to Forum integration"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi import HTTPException

from app.routers.news.core import news_to_forum_post
from app.schemas.forum import NewsToForumPostRequest, NewsToForumPostResponse
from app.models.news import News


class TestNewsToForum:
    """Test News to Forum functionality"""

    @pytest.fixture
    def mock_user(self):
        """Create mock user"""
        user = MagicMock()
        user.id = 1
        user.username = "testuser"
        return user

    @pytest.fixture
    def mock_news(self):
        """Create mock news"""
        news = MagicMock(spec=News)
        news.id = 123
        news.title = "测试新闻标题"
        news.summary = "这是新闻的摘要内容"
        news.source_url = "https://example.com/news/123"
        news.cover_image = "https://example.com/cover.jpg"
        return news

    @pytest.mark.asyncio
    async def test_news_to_forum_success(self, mock_user, mock_news):
        """Test successful news to forum post"""
        from app.schemas.forum import PostCreate

        mock_db = MagicMock()
        mock_db.commit = AsyncMock()

        # Mock news_service.get_published
        with patch('app.routers.news.core.news_service') as mock_news_service:
            mock_news_service.get_published = AsyncMock(return_value=mock_news)

            # Mock forum_service.create_post
            mock_post = MagicMock()
            mock_post.id = 456
            mock_post.title = "讨论：测试新闻标题"

            with patch('app.routers.news.core.forum_service') as mock_forum_service:
                mock_forum_service.create_post = AsyncMock(return_value=mock_post)

                request = NewsToForumPostRequest(
                    news_id=123,
                    title=None,
                    content="我的观点是...",
                    category="general"
                )

                response = await news_to_forum_post(
                    data=request,
                    current_user=mock_user,
                    db=mock_db
                )

                assert response.post_id == 456
                assert response.post_title == "讨论：测试新闻标题"
                assert response.post_url == "/forum/post/456"
                assert "已成功将新闻转发到论坛讨论" in response.message

    @pytest.mark.asyncio
    async def test_news_to_forum_with_custom_title(self, mock_user, mock_news):
        """Test news to forum with custom title"""
        mock_db = MagicMock()
        mock_db.commit = AsyncMock()

        mock_post = MagicMock()
        mock_post.id = 789
        mock_post.title = "自定义讨论标题"

        with patch('app.routers.news.core.news_service') as mock_news_service:
            mock_news_service.get_published = AsyncMock(return_value=mock_news)

            with patch('app.routers.news.core.forum_service') as mock_forum_service:
                mock_forum_service.create_post = AsyncMock(return_value=mock_post)

                request = NewsToForumPostRequest(
                    news_id=123,
                    title="自定义讨论标题",
                    content=None,
                    category="law"
                )

                response = await news_to_forum_post(
                    data=request,
                    current_user=mock_user,
                    db=mock_db
                )

                assert response.post_id == 789
                assert response.post_title == "自定义讨论标题"

    @pytest.mark.asyncio
    async def test_news_to_forum_news_not_found(self, mock_user):
        """Test news to forum when news not found"""
        mock_db = MagicMock()

        with patch('app.routers.news.core.news_service') as mock_news_service:
            mock_news_service.get_published = AsyncMock(return_value=None)

            request = NewsToForumPostRequest(
                news_id=999,
                title=None,
                content="内容",
                category="general"
            )

            with pytest.raises(HTTPException) as exc_info:
                await news_to_forum_post(
                    data=request,
                    current_user=mock_user,
                    db=mock_db
                )

            assert exc_info.value.status_code == 404
            assert "新闻不存在" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_news_to_forum_uses_news_summary(self, mock_user, mock_news):
        """Test that news summary is used when no content provided"""
        mock_db = MagicMock()
        mock_db.commit = AsyncMock()

        mock_post = MagicMock()
        mock_post.id = 100
        mock_post.title = "讨论：测试新闻标题"

        captured_post_data = None

        async def capture_post(db, user_id, post_data):
            nonlocal captured_post_data
            captured_post_data = post_data
            return mock_post

        with patch('app.routers.news.core.news_service') as mock_news_service:
            mock_news_service.get_published = AsyncMock(return_value=mock_news)

            with patch('app.routers.news.core.forum_service') as mock_forum_service:
                mock_forum_service.create_post = capture_post

                request = NewsToForumPostRequest(
                    news_id=123,
                    title=None,
                    content=None,  # No custom content
                    category="general"
                )

                await news_to_forum_post(
                    data=request,
                    current_user=mock_user,
                    db=mock_db
                )

                # Verify summary was used
                assert captured_post_data is not None
                assert "这是新闻的摘要内容" in captured_post_data.content
                assert "来源新闻" in captured_post_data.content

    @pytest.mark.asyncio
    async def test_news_to_forum_preserves_cover_image(self, mock_user, mock_news):
        """Test that news cover image is preserved in forum post"""
        mock_db = MagicMock()
        mock_db.commit = AsyncMock()

        mock_post = MagicMock()
        mock_post.id = 200
        mock_post.title = "讨论：测试新闻标题"

        captured_post_data = None

        async def capture_post(db, user_id, post_data):
            nonlocal captured_post_data
            captured_post_data = post_data
            return mock_post

        with patch('app.routers.news.core.news_service') as mock_news_service:
            mock_news_service.get_published = AsyncMock(return_value=mock_news)

            with patch('app.routers.news.core.forum_service') as mock_forum_service:
                mock_forum_service.create_post = capture_post

                request = NewsToForumPostRequest(
                    news_id=123,
                    title=None,
                    content="我的观点",
                    category="general"
                )

                await news_to_forum_post(
                    data=request,
                    current_user=mock_user,
                    db=mock_db
                )

                # Verify cover image was preserved
                assert captured_post_data is not None
                assert captured_post_data.cover_image == "https://example.com/cover.jpg"


class TestNewsToForumSchemas:
    """Test News to Forum schema validation"""

    def test_news_to_forum_request_minimal(self):
        """Test minimal request (only required fields)"""
        request = NewsToForumPostRequest(news_id=1)
        assert request.news_id == 1
        assert request.title is None
        assert request.content is None
        assert request.category == "general"

    def test_news_to_forum_request_full(self):
        """Test full request with all fields"""
        request = NewsToForumPostRequest(
            news_id=1,
            title="自定义标题",
            content="我的观点",
            category="law"
        )
        assert request.news_id == 1
        assert request.title == "自定义标题"
        assert request.content == "我的观点"
        assert request.category == "law"

    def test_news_to_forum_response(self):
        """Test response schema"""
        response = NewsToForumPostResponse(
            post_id=123,
            post_title="测试标题",
            post_url="/forum/post/123",
            message="成功"
        )
        assert response.post_id == 123
        assert response.post_title == "测试标题"
        assert response.post_url == "/forum/post/123"
        assert response.message == "成功"
