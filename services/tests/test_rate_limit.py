"""限流中间件单元测试"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from services.common.middleware.rate_limit import (
    RateLimiter,
    rate_limiter,
    check_request_rate_limit,
    check_register_rate_limit,
    DEFAULT_RATE_LIMIT_RULES,
    REGISTER_IP_LIMIT,
    REGISTER_PHONE_LIMIT,
)


class MockRedisClient:
    """模拟 Redis 客户端"""

    def __init__(self):
        self._data = {}
        self._ttl = {}
        self._ping_called = False

    async def ping(self):
        self._ping_called = True
        return True

    async def get(self, key):
        if key in self._data:
            return str(self._data[key])
        return None

    async def setex(self, key, ttl, value):
        self._data[key] = value
        self._ttl[key] = ttl

    async def incr(self, key):
        if key in self._data:
            self._data[key] += 1
        else:
            self._data[key] = 1
        return self._data[key]

    async def ttl(self, key):
        return self._ttl.get(key, -1)

    async def close(self):
        self._data.clear()
        self._ttl.clear()


class TestRateLimiter:
    """限流器测试"""

    @pytest.fixture
    def limiter(self):
        """创建测试限流器"""
        return RateLimiter()

    @pytest.mark.asyncio
    async def test_disabled_limiter_returns_true(self, limiter):
        """测试限流禁用时返回 True"""
        limiter._enabled = False
        result, remaining, limit = await limiter.check_rate_limit(
            user_id="user1",
            path="/api/test",
        )
        assert result is True
        assert remaining is None

    @pytest.mark.asyncio
    async def test_first_request_passes(self, limiter):
        """测试首次请求通过"""
        mock_redis = MockRedisClient()
        limiter._client = mock_redis
        limiter._enabled = True

        result, remaining, limit = await limiter.check_rate_limit(
            user_id="user1",
            path="/api/test",
            rules={"/api/test": (5, 60)},
        )

        assert result is True
        assert remaining == 4
        assert limit == 5

    @pytest.mark.asyncio
    async def test_within_limit_passes(self, limiter):
        """测试在限流额度内通过"""
        mock_redis = MockRedisClient()
        mock_redis._data["rate:/api/test:user1"] = 3
        limiter._client = mock_redis
        limiter._enabled = True

        result, remaining, limit = await limiter.check_rate_limit(
            user_id="user1",
            path="/api/test",
            rules={"/api/test": (5, 60)},
        )

        assert result is True
        assert remaining == 1
        assert limit == 5

    @pytest.mark.asyncio
    async def test_exceed_limit_blocked(self, limiter):
        """测试超出限流额度被阻止"""
        mock_redis = MockRedisClient()
        mock_redis._data["rate:/api/test:user1"] = 5
        mock_redis._ttl["rate:/api/test:user1"] = 30
        limiter._client = mock_redis
        limiter._enabled = True

        result, remaining, limit = await limiter.check_rate_limit(
            user_id="user1",
            path="/api/test",
            rules={"/api/test": (5, 60)},
        )

        assert result is False
        assert remaining == 30
        assert limit == 5

    @pytest.mark.asyncio
    async def test_ip_rate_limit(self, limiter):
        """测试 IP 限流"""
        mock_redis = MockRedisClient()
        mock_redis._data["ip_rate:/api/test:127.0.0.1"] = 2
        limiter._client = mock_redis
        limiter._enabled = True

        result, remaining, limit = await limiter.check_ip_rate_limit(
            ip="127.0.0.1",
            path="/api/test",
            limit=5,
            window=60,
        )

        assert result is True
        assert remaining == 2

    @pytest.mark.asyncio
    async def test_resource_rate_limit(self, limiter):
        """测试资源维度限流"""
        mock_redis = MockRedisClient()
        mock_redis._data["resource_rate:/api/test:phone123"] = 1
        limiter._client = mock_redis
        limiter._enabled = True

        result, remaining, limit = await limiter.check_resource_rate_limit(
            resource_id="phone123",
            path="/api/test",
            limit=3,
            window=86400,
        )

        assert result is True
        assert remaining == 1

    @pytest.mark.asyncio
    async def test_get_remaining(self, limiter):
        """测试获取剩余次数"""
        mock_redis = MockRedisClient()
        mock_redis._data["rate:/api/test:user1"] = 2
        limiter._client = mock_redis
        limiter._enabled = True

        remaining = await limiter.get_remaining(
            user_id="user1",
            path="/api/test",
            rules={"/api/test": (10, 60)},
        )

        assert remaining == 8

    @pytest.mark.asyncio
    async def test_redis_error_falls_through(self, limiter):
        """测试 Redis 错误时不阻止请求"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
        limiter._client = mock_redis
        limiter._enabled = True

        result, remaining, limit = await limiter.check_rate_limit(
            user_id="user1",
            path="/api/test",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_close_client(self, limiter):
        """测试关闭限流器"""
        mock_redis = MockRedisClient()
        limiter._client = mock_redis
        limiter._enabled = True

        await limiter.close()
        assert limiter._client is None

    @pytest.mark.asyncio
    async def test_redis_connection_error_fallback(self, limiter):
        """测试 Redis 连接错误时回退"""
        mock_redis = MagicMock()
        mock_redis.ping = AsyncMock(side_effect=ConnectionError("Connection refused"))
        limiter._client = None
        limiter._enabled = True
        limiter.redis_url = "redis://invalid-host:6379"

        result, _, _ = await limiter.check_rate_limit(
            user_id="user1",
            path="/api/test",
        )

        assert result is True

    def test_default_rate_limit_rules(self):
        """测试默认限流规则"""
        assert "/api/v1/auth/register" in DEFAULT_RATE_LIMIT_RULES
        assert "/api/v1/auth/login" in DEFAULT_RATE_LIMIT_RULES

    def test_register_limits(self):
        """测试注册限流配置"""
        assert REGISTER_IP_LIMIT == (5, 3600)
        assert REGISTER_PHONE_LIMIT == (3, 86400)


class TestCheckRequestRateLimit:
    """请求限流检查测试"""

    @pytest.mark.asyncio
    async def test_get_request_skipped(self):
        """测试 GET 请求被跳过"""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.headers = {"X-User-ID": "user1"}

        # Should not raise any exception
        await check_request_rate_limit(mock_request)

    @pytest.mark.asyncio
    async def test_post_request_checked(self):
        """测试 POST 请求被检查"""
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.headers = {"X-User-ID": "user1"}
        mock_request.client.host = "127.0.0.1"

        # Should not raise exception when within limit
        await check_request_rate_limit(mock_request)

    @pytest.mark.asyncio
    async def test_rate_limited_raises_429(self):
        """测试限流时抛出 429 异常"""
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.headers = {"X-User-ID": "limited_user"}
        mock_request.client.host = "127.0.0.1"

        from fastapi import HTTPException
        with patch("services.common.middleware.rate_limit.rate_limiter") as mock_limiter:
            mock_limiter.check_rate_limit = AsyncMock(
                return_value=(False, 60, 10)
            )

            with pytest.raises(HTTPException) as exc_info:
                await check_request_rate_limit(mock_request)

            assert exc_info.value.status_code == 429
            assert "请求过于频繁" in exc_info.value.detail


class TestCheckRegisterRateLimit:
    """注册限流检查测试"""

    @pytest.mark.asyncio
    async def test_register_ip_limited(self):
        """测试注册 IP 限流"""
        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "10.0.0.1"}
        mock_request.client.host = "10.0.0.1"

        from fastapi import HTTPException
        with patch("services.common.middleware.rate_limit.rate_limiter") as mock_limiter:
            mock_limiter.check_ip_rate_limit = AsyncMock(
                return_value=(False, 3600, 5)
            )

            with pytest.raises(HTTPException) as exc_info:
                await check_register_rate_limit(mock_request)

            assert exc_info.value.status_code == 429
            assert "IP注册过于频繁" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_register_phone_limited(self):
        """测试注册手机号限流"""
        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "10.0.0.2"}
        mock_request.client.host = "10.0.0.2"

        from fastapi import HTTPException
        with patch("services.common.middleware.rate_limit.rate_limiter") as mock_limiter:
            mock_limiter.check_ip_rate_limit = AsyncMock(
                return_value=(True, 4, 5)
            )
            mock_limiter.check_resource_rate_limit = AsyncMock(
                return_value=(False, 86400, 3)
            )

            with pytest.raises(HTTPException) as exc_info:
                await check_register_rate_limit(mock_request, phone="13800138000")

            assert exc_info.value.status_code == 429
            assert "手机号注册尝试过于频繁" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_register_ip_list(self):
        """测试 IP 为列表时的处理"""
        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": ["10.0.0.3", "10.0.0.4"]}
        mock_request.client.host = "10.0.0.3"

        with patch("services.common.middleware.rate_limit.rate_limiter") as mock_limiter:
            mock_limiter.check_ip_rate_limit = AsyncMock(
                return_value=(True, 4, 5)
            )

            await check_register_rate_limit(mock_request)

            # Verify the first IP was used
            args, _ = mock_limiter.check_ip_rate_limit.call_args
            assert args[0] == "10.0.0.3"


class TestSyncRateLimitFunctions:
    """同步限流函数测试"""

    def test_vector_search_rate_limit(self):
        """测试向量搜索限流"""
        from services.common.middleware.rate_limit import check_vector_search_rate_limit
        allowed, remaining = check_vector_search_rate_limit("client1")
        assert allowed is True
        assert remaining == 0

    def test_search_rate_limit(self):
        """测试搜索限流"""
        from services.common.middleware.rate_limit import check_search_rate_limit
        allowed, remaining = check_search_rate_limit("client1")
        assert allowed is True
        assert remaining == 0

    def test_vector_rebuild_rate_limit(self):
        """测试向量重建限流"""
        from services.common.middleware.rate_limit import check_vector_rebuild_rate_limit
        allowed, remaining = check_vector_rebuild_rate_limit("client1")
        assert allowed is True
        assert remaining == 0

    def test_seed_rate_limit(self):
        """测试种子限流"""
        from services.common.middleware.rate_limit import check_seed_rate_limit
        allowed, remaining = check_seed_rate_limit("client1")
        assert allowed is True
        assert remaining == 0

    def test_batch_rate_limit(self):
        """测试批量操作限流"""
        from services.common.middleware.rate_limit import check_batch_rate_limit
        allowed, remaining = check_batch_rate_limit("client1")
        assert allowed is True
        assert remaining == 0
