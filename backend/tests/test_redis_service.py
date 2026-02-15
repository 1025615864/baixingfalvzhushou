"""Redis Service 测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# 导入模块而非具体类
import app.services.redis_service as rs


@pytest.fixture(autouse=True)
def _reset_redis_state():
    """重置 Redis 服务状态"""
    rs._redis_service = None
    rs._settings = None
    if hasattr(rs, '_client'):
        rs._client = None
    rs._is_connected = False
    yield
    # 清理


class TestRedisService:
    """Redis 服务测试类"""

    @pytest.fixture
    def redis_service(self):
        """创建 RedisService 实例"""
        service = rs.RedisService()
        service._client = None
        service._is_connected = False
        return service

    @pytest.mark.asyncio
    async def test_connect_without_redis_url(self, redis_service, monkeypatch):
        """测试无 Redis URL 时连接"""
        mock_settings = MagicMock()
        mock_settings.redis_url = ""
        
        monkeypatch.setattr(rs, '_get_settings', MagicMock(return_value=mock_settings))
        
        await redis_service.connect()
        
        assert redis_service._client is None
        assert redis_service._is_connected is False

    @pytest.mark.asyncio
    async def test_connect_success(self, redis_service, monkeypatch):
        """测试成功连接"""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379"
        
        monkeypatch.setattr(rs, '_get_settings', MagicMock(return_value=mock_settings))
        monkeypatch.setattr(rs.redis, 'from_url', MagicMock(return_value=mock_client))
        
        await redis_service.connect()
        
        assert redis_service._is_connected is True
        assert redis_service._client == mock_client

    @pytest.mark.asyncio
    async def test_connect_failure(self, redis_service, monkeypatch):
        """测试连接失败"""
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379"
        
        monkeypatch.setattr(rs, '_get_settings', MagicMock(return_value=mock_settings))
        monkeypatch.setattr(
            rs.redis,
            "from_url",
            MagicMock(side_effect=Exception("连接失败")),
        )
        
        await redis_service.connect()
        
        assert redis_service._is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self, redis_service):
        """测试断开连接"""
        mock_client = AsyncMock()
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        await redis_service.disconnect()
        
        mock_client.close.assert_called_once()
        assert redis_service._client is None
        assert redis_service._is_connected is False

    @pytest.mark.asyncio
    async def test_is_connected_property(self, redis_service):
        """测试 is_connected 属性"""
        assert redis_service.is_connected is False
        
        redis_service._is_connected = True
        assert redis_service.is_connected is True

    @pytest.mark.asyncio
    async def test_get_not_connected(self, redis_service):
        """测试未连接时获取缓存"""
        result = await redis_service.get("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_success(self, redis_service):
        """测试成功获取缓存"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value="test_value")
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        result = await redis_service.get("test_key")
        
        assert result == "test_value"
        mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_error(self, redis_service):
        """测试获取缓存错误"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Redis 错误"))
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        result = await redis_service.get("test_key")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set_not_connected(self, redis_service):
        """测试未连接时设置缓存"""
        result = await redis_service.set("test_key", "test_value")
        assert result is False

    @pytest.mark.asyncio
    async def test_set_success(self, redis_service):
        """测试成功设置缓存"""
        mock_client = AsyncMock()
        mock_client.set = AsyncMock()
        mock_client.setex = AsyncMock()
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        result = await redis_service.set("test_key", "test_value", expire_seconds=3600)
        
        assert result is True
        mock_client.setex.assert_called_once_with("test_key", 3600, "test_value")

    @pytest.mark.asyncio
    async def test_set_without_expire(self, redis_service):
        """测试设置缓存不过期"""
        mock_client = AsyncMock()
        mock_client.set = AsyncMock()
        mock_client.setex = AsyncMock()
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        await redis_service.set("test_key", "test_value")
        
        mock_client.set.assert_called_once_with("test_key", "test_value")

    @pytest.mark.asyncio
    async def test_delete_not_connected(self, redis_service):
        """测试未连接时删除缓存"""
        result = await redis_service.delete("test_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self, redis_service):
        """测试成功删除缓存"""
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock()
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        result = await redis_service.delete("test_key")
        
        assert result is True
        mock_client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists_not_connected(self, redis_service):
        """测试未连接时检查存在"""
        result = await redis_service.exists("test_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_success(self, redis_service):
        """测试成功检查存在"""
        mock_client = AsyncMock()
        mock_client.exists = AsyncMock(return_value=1)
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        result = await redis_service.exists("test_key")
        
        assert result is True
        mock_client.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_expire_not_connected(self, redis_service):
        """测试未连接时设置过期"""
        result = await redis_service.expire("test_key", 3600)
        assert result is False

    @pytest.mark.asyncio
    async def test_expire_success(self, redis_service):
        """测试成功设置过期"""
        mock_client = AsyncMock()
        mock_client.expire = AsyncMock(return_value=True)
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        result = await redis_service.expire("test_key", 3600)
        
        assert result is True
        mock_client.expire.assert_called_once_with("test_key", 3600)

    @pytest.mark.asyncio
    async def test_incr_not_connected(self, redis_service):
        """测试未连接时递增"""
        result = await redis_service.incr("test_key")
        assert result == 0

    @pytest.mark.asyncio
    async def test_incr_success(self, redis_service):
        """测试成功递增"""
        mock_client = AsyncMock()
        mock_client.incr = AsyncMock(return_value=1)
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        result = await redis_service.incr("test_key")
        
        assert result == 1
        mock_client.incr.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_json_not_connected(self, redis_service):
        """测试未连接时获取JSON"""
        result = await redis_service.get_json("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_json_success(self, redis_service):
        """测试成功获取JSON"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value='{"key": "value"}')
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        result = await redis_service.get_json("test_key")
        
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_set_json_success(self, redis_service):
        """测试成功设置JSON"""
        mock_client = AsyncMock()
        mock_client.set = AsyncMock()
        mock_client.setex = AsyncMock()
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        result = await redis_service.set_json("test_key", {"key": "value"}, expire_seconds=3600)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_make_key(self, redis_service):
        """测试生成缓存键"""
        key = redis_service.make_key("test", "123", "456")
        assert key == "test:123:456"

    @pytest.mark.asyncio
    async def test_get_cache_key(self, redis_service):
        """测试获取缓存键"""
        key = redis_service.get_cache_key("user_balance", user_id=123)
        assert key == "points:balance:123"

    @pytest.mark.asyncio
    async def test_publish_not_connected(self, redis_service):
        """测试未连接时发布消息"""
        result = await redis_service.publish("channel", {"message": "test"})
        assert result == 0

    @pytest.mark.asyncio
    async def test_publish_success(self, redis_service):
        """测试成功发布消息"""
        mock_client = AsyncMock()
        mock_client.publish = AsyncMock(return_value=1)
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        result = await redis_service.publish("channel", {"message": "test"})
        
        assert result == 1

    @pytest.mark.asyncio
    async def test_acquire_lock_not_connected(self, redis_service):
        """测试未连接时获取锁"""
        result = await redis_service.acquire_lock("test_lock")
        assert result is None

    @pytest.mark.asyncio
    async def test_acquire_lock_success(self, redis_service):
        """测试成功获取锁"""
        mock_client = AsyncMock()
        mock_client.set = AsyncMock(return_value=True)
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        result = await redis_service.acquire_lock("test_lock", timeout=1)
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_release_lock_not_connected(self, redis_service):
        """测试未连接时释放锁"""
        result = await redis_service.release_lock("test_lock", "lock_id")
        assert result is False

    @pytest.mark.asyncio
    async def test_release_lock_success(self, redis_service):
        """测试成功释放锁"""
        mock_client = AsyncMock()
        mock_client.eval = AsyncMock(return_value=1)
        
        redis_service._client = mock_client
        redis_service._is_connected = True
        
        result = await redis_service.release_lock("test_lock", "lock_id")
        
        assert result is True


class TestPointsCache:
    """PointsCache 测试类"""

    @pytest.fixture
    def points_cache(self):
        """创建 PointsCache 实例"""
        redis_service = rs.RedisService()
        redis_service._client = None
        redis_service._is_connected = False
        return rs.PointsCache(redis_service)

    @pytest.mark.asyncio
    async def test_get_user_balance_not_connected(self, points_cache):
        """测试未连接时获取用户积分"""
        result = await points_cache.get_user_balance(123)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_user_balance(self, points_cache):
        """测试设置用户积分"""
        mock_client = AsyncMock()
        mock_client.set = AsyncMock()
        mock_client.setex = AsyncMock()
        
        points_cache.redis._client = mock_client
        points_cache.redis._is_connected = True
        
        await points_cache.set_user_balance(123, 1000)
        
        mock_client.setex.assert_called()

    @pytest.mark.asyncio
    async def test_invalidate_user_balance(self, points_cache):
        """测试清除用户积分缓存"""
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock()
        
        points_cache.redis._client = mock_client
        points_cache.redis._is_connected = True
        
        await points_cache.invalidate_user_balance(123)
        
        mock_client.delete.assert_called()


class TestCachedDecorator:
    """缓存装饰器测试类"""

    @pytest.mark.asyncio
    async def test_cached_decorator_miss(self, monkeypatch):
        """测试缓存未命中"""
        mock_redis = AsyncMock()
        mock_redis.get_json = AsyncMock(return_value=None)
        mock_redis.set_json = AsyncMock()
        
        monkeypatch.setattr(rs, 'get_redis_service', MagicMock(return_value=mock_redis))
        
        @rs.cached(expire_seconds=60, key_prefix="test")
        async def test_func():
            return "result"
        
        result = await test_func()
        
        assert result == "result"
        mock_redis.set_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_cached_decorator_hit(self, monkeypatch):
        """测试缓存命中"""
        mock_redis = AsyncMock()
        mock_redis.get_json = AsyncMock(return_value={"cached": True})
        mock_redis.set_json = AsyncMock()
        
        monkeypatch.setattr(rs, 'get_redis_service', MagicMock(return_value=mock_redis))
        
        @rs.cached(expire_seconds=60, key_prefix="test")
        async def test_func():
            return "result"
        
        result = await test_func()
        
        assert result == {"cached": True}
        mock_redis.set_json.assert_not_called()
