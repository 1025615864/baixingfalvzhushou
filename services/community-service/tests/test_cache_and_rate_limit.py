"""缓存失效与限流测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


class TestCacheInvalidation:
    """缓存失效正确性测试"""

    @pytest.fixture
    def mock_redis(self):
        mock = AsyncMock()
        mock.get = AsyncMock(return_value=None)
        mock.setex = AsyncMock()
        mock.delete = AsyncMock()
        mock.keys = AsyncMock(return_value=[])
        return mock

    @pytest.mark.asyncio
    async def test_invalidate_post_detail(self, mock_redis):
        """测试帖子详情缓存失效"""
        from app.cache.post_cache import PostCache
        with patch("app.cache.post_cache.redis") as mock_redis_module:
            mock_redis_module.from_url.return_value = mock_redis
            cache = PostCache()
            await cache.invalidate_post(123)
            mock_redis.delete.assert_called_once_with("post:detail:123")

    @pytest.mark.asyncio
    async def test_invalidate_post_list_with_category(self, mock_redis):
        """测试帖子列表缓存失效（指定分类）"""
        from app.cache.post_cache import PostCache
        with patch("app.cache.post_cache.redis") as mock_redis_module:
            mock_redis_module.from_url.return_value = mock_redis
            mock_redis.keys = AsyncMock(return_value=["post:list:law:hot:1"])
            cache = PostCache()
            await cache.invalidate_post_list(category="law")
            mock_redis.keys.assert_called()

    @pytest.mark.asyncio
    async def test_invalidate_post_list_all(self, mock_redis):
        """测试帖子列表缓存失效（全分类）"""
        from app.cache.post_cache import PostCache
        with patch("app.cache.post_cache.redis") as mock_redis_module:
            mock_redis_module.from_url.return_value = mock_redis
            mock_redis.keys = AsyncMock(return_value=["post:list:1", "post:list:2"])
            cache = PostCache()
            await cache.invalidate_post_list()
            mock_redis.keys.assert_called()

    @pytest.mark.asyncio
    async def test_set_post_detail_caches(self, mock_redis):
        """测试设置帖子详情缓存"""
        from app.cache.post_cache import PostCache
        with patch("app.cache.post_cache.redis") as mock_redis_module:
            mock_redis_module.from_url.return_value = mock_redis
            cache = PostCache()
            post_data = {"id": 1, "title": "Test"}
            await cache.set_post_detail(1, post_data)
            mock_redis.setex.assert_called_once()


class TestRateLimiter:
    """限流阈值测试"""

    @pytest.fixture
    def mock_redis(self):
        mock = AsyncMock()
        mock.incr = AsyncMock(return_value=1)
        mock.expire = AsyncMock()
        mock.get = AsyncMock(return_value=None)
        return mock

    def test_rate_limit_initialization(self):
        """测试限流器初始化"""
        from app.middleware.rate_limit import rate_limiter
        assert rate_limiter is not None
        assert rate_limiter.redis_url is not None

    @pytest.mark.asyncio
    async def test_check_post_rate_first_request(self, mock_redis):
        """测试首次发帖请求通过限流"""
        from app.middleware.rate_limit import rate_limiter
        with patch("app.middleware.rate_limit.redis") as mock_redis_module:
            mock_redis_module.from_url.return_value = mock_redis
            result = await rate_limiter.check_post_rate(123)
            assert result is True
            mock_redis.incr.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_comment_rate_multiple(self, mock_redis):
        """测试评论限流（多条）"""
        from app.middleware.rate_limit import rate_limiter
        with patch("app.middleware.rate_limit.redis") as mock_redis_module:
            mock_redis_module.from_url.return_value = mock_redis
            for i in range(5):
                mock_redis.incr = AsyncMock(return_value=i+1)
                result = await rate_limiter.check_comment_rate(123)
                assert result is True

    @pytest.mark.asyncio
    async def test_check_report_rate_limit(self, mock_redis):
        """测试举报限流"""
        from app.middleware.rate_limit import rate_limiter
        with patch("app.middleware.rate_limit.redis") as mock_redis_module:
            mock_redis_module.from_url.return_value = mock_redis
            mock_redis.incr = AsyncMock(return_value=11)
            result = await rate_limiter.check_report_rate(123)
            assert result is False


class TestErrorResponses:
    """错误码一致性测试"""

    def test_post_not_found_error(self):
        """测试帖子不存在错误码"""
        from app.errors.error_codes import ErrorCode
        code, message = ErrorCode.POST_NOT_FOUND
        assert code == "C40401"
        assert "不存在" in message

    def test_permission_denied_error(self):
        """测试权限拒绝错误码"""
        from app.errors.error_codes import ErrorCode
        code, message = ErrorCode.POST_NO_PERMISSION
        assert code == "C40301"
        assert "无权" in message

    def test_rate_limited_error(self):
        """测试限流错误码"""
        from app.errors.error_codes import ErrorCode
        code, message = ErrorCode.RATE_LIMITED
        assert code == "C42901"
        assert "频繁" in message

    def test_content_blocked_error(self):
        """测试内容被封禁错误码"""
        from app.errors.error_codes import ErrorCode
        code, message = ErrorCode.CONTENT_BLOCKED
        assert code == "C42201"

    def test_community_exception_creation(self):
        """测试社区异常创建"""
        from app.errors.error_codes import CommunityException, ErrorCode
        exc = CommunityException(ErrorCode.POST_NOT_FOUND)
        assert exc.code == "C40401"
        assert exc.message == "帖子不存在"
        assert exc.status_code == 404

    def test_community_exception_with_detail(self):
        """测试带详情的社区异常"""
        from app.errors.error_codes import CommunityException, ErrorCode
        exc = CommunityException(ErrorCode.POST_NO_PERMISSION, detail="自定义详情")
        assert exc.detail == "自定义详情"


class TestModerationQueueIntegration:
    """审核队列集成测试"""

    @pytest.mark.asyncio
    async def test_auto_submit_priority_calculation(self):
        """测试AI置信度到优先级的转换"""
        from app.services.moderation_queue_service import ModerationService
        from unittest.mock import MagicMock

        mock_db = AsyncMock()
        service = ModerationService(mock_db)

        with patch.object(service, "add_to_queue", new_callable=AsyncMock) as mock_add:
            await service.auto_submit_for_review(
                content_type="post",
                content_id=1,
                content_preview="test",
                ai_confidence=0.95,
                ai_analysis="blocked content"
            )
            mock_add.assert_called_once()
            call_args = mock_add.call_args
            assert call_args.kwargs["priority"] == 1

    @pytest.mark.asyncio
    async def test_review_approve_updates_content(self):
        """测试审核通过更新内容状态"""
        from app.services.moderation_queue_service import ModerationService
        from app.models.moderation import ModerationQueue
        from unittest.mock import MagicMock, AsyncMock

        mock_db = AsyncMock()
        mock_item = MagicMock()
        mock_item.content_type = "post"
        mock_item.content_id = 1
        mock_item.status = "pending"

        mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_item)))
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = ModerationService(mock_db)
        result = await service.review(
            item_id=1,
            decision="approve",
            reviewer_id=1,
            reason="OK"
        )
        assert result.status == "reviewed"
        assert result.review_decision == "approve"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
