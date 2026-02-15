"""Tests for cache_service.py"""
import asyncio
import json
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.cache_service import CacheService, cache_service, _memory_cache, cached


@pytest.fixture
def cache():
    """Create a fresh CacheService instance for each test"""
    # Clear memory cache before each test
    _memory_cache.clear()
    service = CacheService()
    yield service
    # Cleanup after test
    _memory_cache.clear()
    service._connected = False
    service._redis = None


def _disable_redis(cache: CacheService) -> None:
    cache._connected = False
    cache._redis = None


def _enable_redis(cache: CacheService, redis_client=None):
    cache._connected = True
    cache._redis = redis_client if redis_client is not None else AsyncMock()
    return cache._redis


def _set_memory_cache(key: str, value, ttl: float = 300) -> None:
    _memory_cache[key] = (value, time.time() + ttl)


@pytest.mark.asyncio
async def test_cache_service_init(cache):
    """Test CacheService initialization"""
    assert cache._redis is None
    assert cache._connected is False


@pytest.mark.asyncio
async def test_is_connected_property(cache):
    """Test is_connected property"""
    assert cache.is_connected is False
    
    cache._connected = True
    assert cache.is_connected is True
    
    cache._connected = False
    assert cache.is_connected is False


@pytest.mark.asyncio
async def test_redis_property(cache):
    """Test redis property"""
    assert cache.redis is None
    
    _enable_redis(cache, MagicMock())
    assert cache.redis is not None
    
    _disable_redis(cache)
    assert cache.redis is None


@pytest.mark.asyncio
async def test_connect_success(cache):
    """Test successful Redis connection"""
    mock_redis_client = AsyncMock()
    mock_redis_client.ping = AsyncMock()
    
    # Mock the redis.asyncio.from_url method directly
    with patch('redis.asyncio.from_url', return_value=mock_redis_client):
        result = await cache.connect("redis://localhost:6379")
        
        assert result is True
        assert cache._connected is True
        assert cache._redis is not None
        mock_redis_client.ping.assert_called_once()


@pytest.mark.asyncio
async def test_connect_import_error(cache):
    """Test Redis connection with ImportError"""
    mock_asyncio_module = MagicMock()
    mock_asyncio_module.from_url.side_effect = ImportError("No module named 'redis'")
    
    with patch.dict('sys.modules', {'redis.asyncio': mock_asyncio_module}):
        result = await cache.connect("redis://localhost:6379")
        
        assert result is False
        assert cache._connected is False


@pytest.mark.asyncio
async def test_connect_general_error(cache):
    """Test Redis connection with general exception"""
    mock_asyncio_module = MagicMock()
    mock_asyncio_module.from_url.side_effect = Exception("Connection refused")
    
    with patch.dict('sys.modules', {'redis.asyncio': mock_asyncio_module}):
        result = await cache.connect("redis://localhost:6379")
        
        assert result is False
        assert cache._connected is False


@pytest.mark.asyncio
async def test_disconnect(cache):
    """Test disconnecting from Redis"""
    mock_redis = AsyncMock()
    cache._redis = mock_redis
    cache._connected = True
    
    await cache.disconnect()
    
    mock_redis.close.assert_called_once()
    assert cache._connected is False


@pytest.mark.asyncio
async def test_get_redis_success(cache):
    """Test getting cache value when Redis is connected"""
    redis_client = _enable_redis(cache)
    redis_client.get = AsyncMock(return_value="test_value")
    
    result = await cache.get("test_key")
    
    assert result == "test_value"
    redis_client.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_get_redis_error(cache):
    """Test getting cache value with Redis error, fallback to memory"""
    redis_client = _enable_redis(cache)
    redis_client.get = AsyncMock(side_effect=Exception("Redis error"))
    
    # Add to memory cache
    _set_memory_cache("test_key", "memory_value")
    
    result = await cache.get("test_key")
    
    assert result == "memory_value"


@pytest.mark.asyncio
async def test_get_memory_expired(cache):
    """Test getting expired cache from memory"""
    _disable_redis(cache)
    
    # Add expired entry to memory cache
    _set_memory_cache("expired_key", "old_value", ttl=-1)
    
    result = await cache.get("expired_key")
    
    assert result is None
    assert "expired_key" not in _memory_cache


@pytest.mark.asyncio
async def test_get_not_found(cache):
    """Test getting non-existent key"""
    _disable_redis(cache)
    
    result = await cache.get("nonexistent_key")
    
    assert result is None


@pytest.mark.asyncio
async def test_set_redis_success(cache):
    """Test setting cache value when Redis is connected"""
    redis_client = _enable_redis(cache)
    redis_client.setex = AsyncMock()
    
    result = await cache.set("test_key", "test_value", expire=300)
    
    assert result is True
    redis_client.setex.assert_called_once_with("test_key", 300, "test_value")


@pytest.mark.asyncio
async def test_set_redis_error(cache):
    """Test setting cache value with Redis error, fallback to memory"""
    redis_client = _enable_redis(cache)
    redis_client.setex = AsyncMock(side_effect=Exception("Redis error"))
    
    result = await cache.set("test_key", "test_value", expire=300)
    
    assert result is True
    assert "test_key" in _memory_cache


@pytest.mark.asyncio
async def test_set_memory_only(cache):
    """Test setting cache value in memory only (no Redis)"""
    _disable_redis(cache)
    
    result = await cache.set("memory_key", "memory_value", expire=300)
    
    assert result is True
    assert "memory_key" in _memory_cache


@pytest.mark.asyncio
async def test_delete_redis_success(cache):
    """Test deleting cache value when Redis is connected"""
    redis_client = _enable_redis(cache)
    redis_client.delete = AsyncMock(return_value=1)
    
    result = await cache.delete("test_key")
    
    assert result is True
    redis_client.delete.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_delete_redis_error(cache):
    """Test deleting cache value with Redis error"""
    redis_client = _enable_redis(cache)
    redis_client.delete = AsyncMock(side_effect=Exception("Redis error"))
    
    # Also add to memory cache to test it gets deleted
    _set_memory_cache("test_key", "value")
    
    result = await cache.delete("test_key")
    
    assert result is True
    assert "test_key" not in _memory_cache


@pytest.mark.asyncio
async def test_delete_memory_only(cache):
    """Test deleting cache value from memory only (no Redis)"""
    _disable_redis(cache)
    _set_memory_cache("memory_key", "value")
    
    result = await cache.delete("memory_key")
    
    assert result is True
    assert "memory_key" not in _memory_cache


@pytest.mark.asyncio
async def test_get_json_valid_dict(cache):
    """Test getting valid JSON dict from cache"""
    _disable_redis(cache)
    _set_memory_cache("json_key", json.dumps({"key": "value"}, ensure_ascii=False))
    
    result = await cache.get_json("json_key")
    
    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_get_json_valid_list(cache):
    """Test getting valid JSON list from cache"""
    _disable_redis(cache)
    _set_memory_cache("json_key", json.dumps([1, 2, 3], ensure_ascii=False))
    
    result = await cache.get_json("json_key")
    
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_get_json_invalid_json(cache):
    """Test getting invalid JSON from cache"""
    _disable_redis(cache)
    _set_memory_cache("json_key", "invalid json{")
    
    result = await cache.get_json("json_key")
    
    assert result is None


@pytest.mark.asyncio
async def test_get_json_not_found(cache):
    """Test getting non-existent JSON key"""
    _disable_redis(cache)
    
    result = await cache.get_json("nonexistent")
    
    assert result is None


@pytest.mark.asyncio
async def test_get_json_invalid_type(cache):
    """Test getting JSON that is valid but not dict or list"""
    _disable_redis(cache)
    # JSON is valid but it's a string, not dict or list
    _set_memory_cache("json_key", "\"just a string\"")
    
    result = await cache.get_json("json_key")
    
    assert result is None


@pytest.mark.asyncio
async def test_set_json(cache):
    """Test setting JSON cache"""
    _disable_redis(cache)
    
    test_data = {"key": "value", "list": [1, 2, 3]}
    result = await cache.set_json("json_key", test_data, expire=300)
    
    assert result is True
    assert "json_key" in _memory_cache
    stored_value, expires_at = _memory_cache["json_key"]
    assert json.loads(stored_value) == test_data


@pytest.mark.asyncio
async def test_clear_pattern_redis(cache):
    """Test clearing cache by pattern when Redis is connected"""
    redis_client = _enable_redis(cache)
    
    # Mock scan_iter to yield keys
    async def mock_scan_iter(match):
        keys = ["pattern:key1", "pattern:key2"]
        for key in keys:
            yield key
    
    redis_client.scan_iter = mock_scan_iter
    redis_client.delete = AsyncMock(return_value=2)
    
    result = await cache.clear_pattern("pattern:*")
    
    assert result == 2
    redis_client.delete.assert_called_once()


@pytest.mark.asyncio
async def test_clear_pattern_redis_error(cache):
    """Test clearing cache by pattern with Redis error"""
    redis_client = _enable_redis(cache)
    redis_client.scan_iter = AsyncMock(side_effect=Exception("Redis error"))
    
    result = await cache.clear_pattern("pattern:*")
    
    assert result == 0


@pytest.mark.asyncio
async def test_clear_pattern_memory(cache):
    """Test clearing cache by pattern in memory"""
    _disable_redis(cache)
    
    # Add keys matching pattern
    _set_memory_cache("pattern:key1", "value1")
    _set_memory_cache("pattern:key2", "value2")
    _set_memory_cache("other:key", "value3")
    
    result = await cache.clear_pattern("pattern:*")
    
    assert result == 2
    assert "pattern:key1" not in _memory_cache
    assert "pattern:key2" not in _memory_cache
    assert "other:key" in _memory_cache


@pytest.mark.asyncio
async def test_clear_pattern_memory_no_match(cache):
    """Test clearing cache by pattern with no matching keys"""
    _disable_redis(cache)
    _set_memory_cache("other:key", "value")
    
    result = await cache.clear_pattern("nomatch:*")
    
    assert result == 0


@pytest.mark.asyncio
async def test_setnx_redis_success(cache):
    """Test setnx when key doesn't exist (Redis connected)"""
    redis_client = _enable_redis(cache)
    redis_client.set = AsyncMock(return_value=True)
    
    result = await cache.setnx("new_key", "value", expire=300)
    
    assert result is True
    redis_client.set.assert_called_once()


@pytest.mark.asyncio
async def test_setnx_redis_key_exists(cache):
    """Test setnx when key already exists (Redis connected)"""
    redis_client = _enable_redis(cache)
    redis_client.set = AsyncMock(return_value=None)
    
    result = await cache.setnx("existing_key", "value", expire=300)
    
    assert result is False


@pytest.mark.asyncio
async def test_setnx_redis_error(cache):
    """Test setnx with Redis error - should fallback to memory cache"""
    # 清理内存缓存，确保测试隔离
    _memory_cache.clear()
    
    redis_client = _enable_redis(cache)
    redis_client.set = AsyncMock(side_effect=Exception("Redis error"))
    
    result = await cache.setnx("key", "value", expire=300)
    
    # Redis 错误时回退到内存缓存，应该成功
    assert result is True
    assert "key" in _memory_cache


@pytest.mark.asyncio
async def test_setnx_memory_success(cache):
    """Test setnx in memory (key doesn't exist)"""
    _disable_redis(cache)
    
    result = await cache.setnx("new_key", "value", expire=300)
    
    assert result is True
    assert "new_key" in _memory_cache


@pytest.mark.asyncio
async def test_setnx_memory_key_exists(cache):
    """Test setnx in memory (key exists and not expired)"""
    _disable_redis(cache)
    _set_memory_cache("existing_key", "value")
    
    result = await cache.setnx("existing_key", "new_value", expire=300)
    
    assert result is False


@pytest.mark.asyncio
async def test_setnx_memory_key_expired(cache):
    """Test setnx in memory (key exists but expired)"""
    _disable_redis(cache)
    _set_memory_cache("expired_key", "old_value", ttl=-1)
    
    result = await cache.setnx("expired_key", "new_value", expire=300)
    
    assert result is True
    assert _memory_cache["expired_key"][0] == "new_value"


@pytest.mark.asyncio
async def test_increment_redis_success(cache):
    """Test increment with Redis connected"""
    redis_client = _enable_redis(cache)
    redis_client.incrby = AsyncMock(return_value=5)
    
    result = await cache.increment("counter", 2)
    
    assert result == 5
    redis_client.incrby.assert_called_once_with("counter", 2)


@pytest.mark.asyncio
async def test_increment_redis_error(cache):
    """Test increment with Redis error - should fallback to memory cache"""
    # 清理内存缓存，确保测试隔离
    _memory_cache.clear()
    
    redis_client = _enable_redis(cache)
    redis_client.incrby = AsyncMock(side_effect=Exception("Redis error"))
    
    result = await cache.increment("counter", 1)
    
    # Redis 错误时回退到内存缓存，新键应该返回初始值 1
    assert result == 1
    assert "counter" in _memory_cache


@pytest.mark.asyncio
async def test_increment_memory_success(cache):
    """Test increment in memory"""
    _disable_redis(cache)
    _set_memory_cache("counter", "10")
    
    result = await cache.increment("counter", 5)
    
    assert result == 15
    assert _memory_cache["counter"][0] == "15"


@pytest.mark.asyncio
async def test_increment_memory_not_numeric(cache):
    """Test increment in memory with non-numeric value"""
    _disable_redis(cache)
    _set_memory_cache("counter", "not_a_number")
    
    result = await cache.increment("counter", 1)
    
    assert result == 0


@pytest.mark.asyncio
async def test_increment_memory_new_key(cache):
    """Test increment in memory for new key"""
    _disable_redis(cache)
    
    result = await cache.increment("new_counter", 10)
    
    assert result == 10
    assert "new_counter" in _memory_cache


@pytest.mark.asyncio
async def test_acquire_lock_redis_success(cache):
    """Test acquiring lock with Redis connected"""
    redis_client = _enable_redis(cache)
    redis_client.set = AsyncMock(return_value=True)
    
    result = await cache.acquire_lock("lock_key", "lock_value", expire=60)
    
    assert result is True


@pytest.mark.asyncio
async def test_acquire_lock_redis_already_locked(cache):
    """Test acquiring lock when already locked (Redis)"""
    redis_client = _enable_redis(cache)
    redis_client.set = AsyncMock(return_value=None)
    
    result = await cache.acquire_lock("lock_key", "lock_value", expire=60)
    
    assert result is False


@pytest.mark.asyncio
async def test_acquire_lock_redis_error(cache):
    """Test acquiring lock with Redis error - should fallback to memory cache and return True success"""
    redis_client = _enable_redis(cache)
    redis_client.set = AsyncMock(side_effect=Exception("Redis error"))
    
    # Clear any existing lock in memory cache
    _memory_cache.clear()
    
    result = await cache.acquire_lock("lock_key", "lock_value", expire=60)
    
    # Should fallback to memory cache and succeed
    assert result is True


@pytest.mark.asyncio
async def test_acquire_lock_memory_success(cache):
    """Test acquiring lock in memory"""
    _disable_redis(cache)
    
    result = await cache.acquire_lock("lock_key", "lock_value", expire=60)
    
    assert result is True
    assert "lock_key" in _memory_cache


@pytest.mark.asyncio
async def test_acquire_lock_memory_already_locked(cache):
    """Test acquiring lock in memory when already locked"""
    _disable_redis(cache)
    _set_memory_cache("lock_key", "lock_value")
    
    result = await cache.acquire_lock("lock_key", "different_value", expire=60)
    
    assert result is False


@pytest.mark.asyncio
async def test_acquire_lock_memory_expired(cache):
    """Test acquiring lock in memory when lock expired"""
    _disable_redis(cache)
    _set_memory_cache("lock_key", "old_value", ttl=-1)
    
    result = await cache.acquire_lock("lock_key", "new_value", expire=60)
    
    assert result is True


@pytest.mark.asyncio
async def test_refresh_lock_redis_success(cache):
    """Test refreshing lock with Redis connected"""
    redis_client = _enable_redis(cache)
    redis_client.eval = AsyncMock(return_value=1)
    
    result = await cache.refresh_lock("lock_key", "lock_value", expire=60)
    
    assert result is True


@pytest.mark.asyncio
async def test_refresh_lock_redis_not_found(cache):
    """Test refreshing lock when key not found (Redis)"""
    redis_client = _enable_redis(cache)
    redis_client.eval = AsyncMock(return_value=0)
    
    result = await cache.refresh_lock("lock_key", "lock_value", expire=60)
    
    assert result is False


@pytest.mark.asyncio
async def test_refresh_lock_redis_error(cache):
    """Test refreshing lock with Redis error - should fallback to memory cache and return True (key doesn't exist)"""
    redis_client = _enable_redis(cache)
    redis_client.eval = AsyncMock(side_effect=Exception("Redis error"))
    
    # Clear memory cache first
    _memory_cache.clear()
    
    result = await cache.refresh_lock("lock_key", "lock_value", expire=60)
    
    # Redis error时回退到内存缓存，key不存在时实现返回True（因为第388-390行代码：key不存在返回True）
    assert result is True, f"Expected True when key doesn't exist but got {result}"


@pytest.mark.asyncio
async def test_refresh_lock_memory_success(cache):
    """Test refreshing lock in memory"""
    _disable_redis(cache)
    _set_memory_cache("lock_key", "lock_value")
    
    result = await cache.refresh_lock("lock_key", "lock_value", expire=60)
    
    assert result is True
    assert _memory_cache["lock_key"][0] == "lock_value"


@pytest.mark.asyncio
async def test_refresh_lock_memory_not_found(cache):
    """Test refreshing lock in memory when not found"""
    _disable_redis(cache)
    
    result = await cache.refresh_lock("lock_key", "lock_value", expire=60)
    
    # memory cache实现中，key不存在返回True（因为第388-390行代码：key不存在返回True）
    assert result is True, f"Expected True when key doesn't exist but got {result}"


@pytest.mark.asyncio
async def test_refresh_lock_memory_wrong_value(cache):
    """Test refreshing lock in memory with wrong value"""
    _disable_redis(cache)
    _set_memory_cache("lock_key", "different_value")
    
    result = await cache.refresh_lock("lock_key", "lock_value", expire=60)
    
    assert result is False


@pytest.mark.asyncio
async def test_release_lock_redis_success(cache):
    """Test releasing lock with Redis connected"""
    redis_client = _enable_redis(cache)
    redis_client.eval = AsyncMock(return_value=1)
    
    result = await cache.release_lock("lock_key", "lock_value")
    
    assert result is True


@pytest.mark.asyncio
async def test_release_lock_redis_not_found(cache):
    """Test releasing lock when key not found (Redis)"""
    redis_client = _enable_redis(cache)
    redis_client.eval = AsyncMock(return_value=0)
    
    result = await cache.release_lock("lock_key", "lock_value")
    
    # When key doesn't exist, Redis返回0，实现返回False (第407行int(result or 0) > 0)
    assert result is False


@pytest.mark.asyncio
async def test_release_lock_redis_wrong_value(cache):
    """Test releasing lock with wrong value (Redis)"""
    redis_client = _enable_redis(cache)
    redis_client.eval = AsyncMock(return_value=0)
    
    result = await cache.release_lock("lock_key", "wrong_value")
    
    # When value doesn't match, Redis返回0，实现返回False (第407行int(result or 0) > 0)
    assert result is False


@pytest.mark.asyncio
async def test_release_lock_redis_error(cache):
    """Test releasing lock with Redis error - should fallback to memory cache"""
    redis_client = _enable_redis(cache)
    # 修复：让 set 操作也抛出异常，这样才能触发 fallback 机制
    redis_client.set = AsyncMock(side_effect=Exception("Redis error"))
    redis_client.eval = AsyncMock(side_effect=Exception("Redis error"))
    
    # Clear memory cache first
    _memory_cache.clear()
    
    # Setup: acquire lock first - should succeed in memory since Redis is mocked to fail
    # acquire_lock 在 Redis 错误时会回退到内存缓存
    acquired = await cache.acquire_lock("lock_key", "lock_value", expire=60)
    assert acquired is True, "Acquiring lock should succeed"
    # 验证锁在内存缓存中
    assert "lock_key" in _memory_cache, "Lock should be in memory cache after acquisition"
    
    result = await cache.release_lock("lock_key", "lock_value")
    
    # 应该回退到内存缓存并成功（因为第414-422行的逻辑）
    assert result is True, "Releasing lock should succeed"
    assert "lock_key" not in _memory_cache, "Lock should be removed from memory cache"


@pytest.mark.asyncio
async def test_release_lock_memory_not_found(cache):
    """Test releasing lock in memory when not found"""
    _disable_redis(cache)
    
    result = await cache.release_lock("lock_key", "lock_value")
    
    assert result is True


@pytest.mark.asyncio
async def test_release_lock_memory_success(cache):
    """Test releasing lock in memory"""
    _disable_redis(cache)
    _set_memory_cache("lock_key", "lock_value")
    
    result = await cache.release_lock("lock_key", "lock_value")
    
    assert result is True
    assert "lock_key" not in _memory_cache


@pytest.mark.asyncio
async def test_release_lock_memory_wrong_value(cache):
    """Test releasing lock in memory with wrong value"""
    _disable_redis(cache)
    _set_memory_cache("lock_key", "different_value")
    
    result = await cache.release_lock("lock_key", "lock_value")
    
    # 内存缓存实现中，值不匹配时返回True（第420行注释说明：值不匹配，但锁已存在，视为成功操作）
    assert result is True


@pytest.mark.asyncio
async def test_cached_decorator_cache_hit(cache):
    """Test cached decorator with cache hit"""
    _disable_redis(cache)
    
    @cached("test_prefix", expire=300)
    async def expensive_function(arg1, arg2):
        return {"result": f"{arg1}-{arg2}"}
    
    # First call to populate cache
    result1 = await expensive_function("a", "b")
    assert result1 == {"result": "a-b"}
    
    # Second call should hit cache
    result2 = await expensive_function("a", "b")
    assert result2 == {"result": "a-b"}
    
    # Check that the cache was populated
    cache_keys = [k for k in _memory_cache if k.startswith("test_prefix:")]
    assert len(cache_keys) == 1


@pytest.mark.asyncio
async def test_cached_decorator_cache_miss(cache):
    """Test cached decorator with cache miss"""
    _disable_redis(cache)
    call_count = 0
    
    @cached("miss_prefix", expire=300)
    async def expensive_function(arg):
        nonlocal call_count
        call_count += 1
        return {"count": call_count}
    
    # First call
    result1 = await expensive_function("x")
    assert result1 == {"count": 1}
    
    # Second call with different argument
    result2 = await expensive_function("y")
    assert result2 == {"count": 2}


@pytest.mark.asyncio
async def test_cached_decorator_none_result(cache):
    """Test cached decorator with None result (should not be cached)"""
    _disable_redis(cache)
    
    @cached("none_prefix", expire=300)
    async def function_returns_none(arg):
        return None
    
    result = await function_returns_none("test")
    
    assert result is None
    
    # None results should not be cached
    cache_keys = [k for k in _memory_cache if k.startswith("none_prefix:")]
    assert len(cache_keys) == 0


@pytest.mark.asyncio
async def test_cached_decorator_json_serialization(cache):
    """Test cached decorator with complex JSON data"""
    _disable_redis(cache)
    
    @cached("json_prefix", expire=300)
    async def function_with_json():
        return {"list": [1, 2, 3], "nested": {"key": "value"}}
    
    result = await function_with_json()
    
    assert result == {"list": [1, 2, 3], "nested": {"key": "value"}}
    
    # Verify it was stored as JSON
    cache_keys = [k for k in _memory_cache if k.startswith("json_prefix:")]
    assert len(cache_keys) == 1


def test_type_definitions():
    """Test type aliases and type variables"""
    from app.services.cache_service import JsonDict, JsonList, JsonValue, TJson, P
    
    # Test that type aliases work
    dict_value: JsonDict = {"key": "value"}
    list_value: JsonList = [1, 2, 3]
    
    # JsonValue should accept both
    json_dict: JsonValue = dict_value
    json_list: JsonValue = list_value
    
    # Verify they are correct types
    assert isinstance(json_dict, dict)
    assert isinstance(json_list, list)


def test_singleton_instance():
    """Test that cache_service singleton is properly instantiated"""
    assert isinstance(cache_service, CacheService)
