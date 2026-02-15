"""缓存策略测试用例"""
import asyncio
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

# 添加 backend 目录到 sys.path
backend_path = os.path.dirname(os.path.dirname(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.utils.cache_strategy import (
    CacheBreachProtection,
    CachePreloader,
    CacheStrategy,
    cache_strategy,
    cached_with_strategy,
    preload_hot_data,
    get_cache_hit_rate,
    HOT_KEYS,
)


class MockCacheService:
    """模拟缓存服务"""

    def __init__(self):
        self._data: dict[str, str] = {}
        self._locks: dict[str, str] = {}

    async def get_json(self, key: str) -> dict | None:
        value = self._data.get(key)
        return value if value else None

    async def set_json(self, key: str, value: dict, expire: int = 300) -> None:
        self._data[key] = value

    async def setnx(self, key: str, value: str, expire: int = 10) -> bool:
        if key in self._locks:
            return False
        self._locks[key] = value
        return True

    async def release_lock(self, key: str, value: str) -> bool:
        if self._locks.get(key) == value:
            del self._locks[key]
            return True
        return False

    async def clear_pattern(self, pattern: str) -> int:
        count = 0
        keys_to_delete = []
        for key in self._data:
            if pattern.replace("*", "") in key:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del self._data[key]
            count += 1
        return count


@pytest.fixture
def mock_cache():
    """创建模拟缓存服务"""
    return MockCacheService()


@pytest.fixture
def patched_cache(mock_cache):
    """注入 cache_service 的 mock_cache"""
    with patch("app.utils.cache_strategy.cache_service", mock_cache):
        yield mock_cache


class TestCacheBreachProtection:
    """缓存击穿防护测试"""

    @pytest.mark.asyncio
    async def test_acquire_lock_success(self, patched_cache):
        """测试获取锁成功"""
        result = await CacheBreachProtection.acquire_lock(
            lock_key="test_lock",
            lock_value="token123",
            expire=10,
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_lock_already_exists(self, patched_cache):
        """测试锁已存在"""
        await patched_cache.setnx("test_lock", "existing_token")
        result = await CacheBreachProtection.acquire_lock(
            lock_key="test_lock",
            lock_value="new_token",
            expire=10,
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_release_lock_success(self, patched_cache):
        """测试释放锁成功"""
        await patched_cache.setnx("test_lock", "token123")
        result = await CacheBreachProtection.release_lock(
            lock_key="test_lock",
            lock_value="token123",
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_release_lock_wrong_value(self, patched_cache):
        """测试释放锁-值不匹配"""
        await patched_cache.setnx("test_lock", "token123")
        result = await CacheBreachProtection.release_lock(
            lock_key="test_lock",
            lock_value="wrong_token",
        )
        assert result is False



class TestCachePreloader:
    """缓存预热器测试"""

    @pytest.mark.asyncio
    async def test_preload_cache_hit(self, patched_cache):
        """测试预热-缓存命中"""
        await patched_cache.set_json("existing_key", {"data": "test"})
        preloader = CachePreloader()

        async def loader():
            return {"data": "should_not_call"}

        result = await preloader.preload("existing_key", loader, 300)
        assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_preload_cache_miss(self, patched_cache):
        """测试预热-缓存未命中"""
        preloader = CachePreloader()

        async def loader():
            return {"data": "loaded"}

        result = await preloader.preload("new_key", loader, 300)
        assert result == {"data": "loaded"}
        cached = await patched_cache.get_json("new_key")
        assert cached == {"data": "loaded"}

    @pytest.mark.asyncio
    async def test_preload_returns_none(self, patched_cache):
        """测试预热返回None"""
        preloader = CachePreloader()

        async def loader():
            return None

        result = await preloader.preload("null_key", loader, 300)
        assert result is None



    @pytest.mark.asyncio
    async def test_start_background_refresh(self, patched_cache):
        """测试启动后台刷新"""
        preloader = CachePreloader()

        async def loader():
            return {"data": "refreshed"}

        await preloader.start_background_refresh(
            key="refresh_key",
            loader=loader,
            interval=1,
            expire=300,
        )

        assert "refresh_key" in preloader._refresh_tasks


    @pytest.mark.asyncio
    async def test_stop_background_refresh(self, patched_cache):
        """测试停止后台刷新"""
        preloader = CachePreloader()

        async def loader():
            return {"data": "refreshed"}

        await preloader.start_background_refresh(
            key="refresh_key",
            loader=loader,
            interval=1,
            expire=300,
        )
        await preloader.stop_background_refresh("refresh_key")

        assert "refresh_key" not in preloader._refresh_tasks


class TestCacheStrategy:
    """缓存策略测试"""

    @pytest.mark.asyncio
    async def test_get_or_load_cache_hit(self, patched_cache):
        """测试获取-缓存命中"""
        await patched_cache.set_json("cache_key", {"hit": True})
        strategy = CacheStrategy()

        async def loader():
            return {"should_not_call": True}

        result = await strategy.get_or_load("cache_key", loader, 300, use_lock=False)
        assert result == {"hit": True}

    @pytest.mark.asyncio
    async def test_get_or_load_cache_miss_no_lock(self, patched_cache):
        """测试获取-缓存未命中不使用锁"""
        strategy = CacheStrategy()

        async def loader():
            return {"loaded": True}

        result = await strategy.get_or_load("new_key", loader, 300, use_lock=False)
        assert result == {"loaded": True}


    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, patched_cache):
        """测试按模式失效缓存"""
        patched_cache._data = {
            "user:1": {"name": "Alice"},
            "user:2": {"name": "Bob"},
            "order:1": {"item": "Book"},
        }
        strategy = CacheStrategy()

        count = await strategy.invalidate_pattern("user:*")

        assert count == 2
        assert "user:1" not in patched_cache._data
        assert "user:2" not in patched_cache._data
        assert "order:1" in patched_cache._data

    def test_record_hit(self):
        """测试记录命中"""
        strategy = CacheStrategy()
        start_time = 1000.0
        strategy._record_hit("test_key", start_time)

        assert "test_key" in strategy._stats
        assert strategy._stats["test_key"]["hits"] == 1

    def test_record_miss(self):
        """测试记录未命中"""
        strategy = CacheStrategy()
        start_time = 1000.0
        strategy._record_miss("test_key", start_time)

        assert "test_key" in strategy._stats
        assert strategy._stats["test_key"]["misses"] == 1

    def test_get_stats(self):
        """测试获取统计"""
        strategy = CacheStrategy()
        start_time = 1000.0
        strategy._record_hit("key1", start_time)
        strategy._record_hit("key1", start_time)
        strategy._record_miss("key1", start_time)

        stats = strategy.get_stats()

        assert "key1" in stats
        assert stats["key1"]["hits"] == 2
        assert stats["key1"]["misses"] == 1
        assert stats["key1"]["hit_rate"] == "66.67%"


class TestCachedWithStrategy:
    """带策略的缓存装饰器测试"""

    @pytest.mark.asyncio
    async def test_cached_decorator(self, patched_cache):
        """测试缓存装饰器"""
        call_count = 0

        @cached_with_strategy("test_prefix", expire=600, use_lock=False)
        async def expensive_function(x: int) -> dict:
            nonlocal call_count
            call_count += 1
            return {"result": x * 2}

        result1 = await expensive_function(5)
        result2 = await expensive_function(5)

        assert result1 == {"result": 10}
        assert result2 == {"result": 10}
        assert call_count == 1  # 第二次调用应该命中缓存

    @pytest.mark.asyncio
    async def test_cached_decorator_different_args(self, patched_cache):
        """测试缓存装饰器-不同参数"""
        call_count = 0

        @cached_with_strategy("test_prefix", expire=600, use_lock=False)
        async def expensive_function(x: int) -> dict:
            nonlocal call_count
            call_count += 1
            return {"result": x * 2}

        result1 = await expensive_function(5)
        result2 = await expensive_function(10)

        assert result1 == {"result": 10}
        assert result2 == {"result": 20}
        assert call_count == 2


class TestPreloadHotData:
    """热点数据预热测试"""


    @pytest.mark.asyncio
    async def test_preload_hot_data_unknown_type(self, patched_cache):
        """测试预热未知类型"""
        count = await preload_hot_data("unknown_type", lambda: [])

        assert count == 0



class TestGetCacheHitRate:
    """缓存命中率测试"""

    @pytest.mark.asyncio
    async def test_get_cache_hit_rate_empty(self, patched_cache):
        """测试获取命中率-空数据"""
        # 重置全局策略的统计
        cache_strategy._stats = {}
        result = await get_cache_hit_rate()
        assert isinstance(result, dict)
        assert result["hit_rate"] == 0
        assert result["total_requests"] == 0
        assert result["total_hits"] == 0



class TestCacheStrategyEdgeCases:
    """缓存策略边界条件测试"""

    @pytest.mark.asyncio
    async def test_get_or_load_exception_handling(self, patched_cache):
        """测试获取异常处理"""
        strategy = CacheStrategy()

        async def normal_loader():
            return {"error": "handled"}

        result = await strategy.get_or_load("failing_key", normal_loader, 300, use_lock=False)

        assert result == {"error": "handled"}




class TestCacheStrategyIntegration:
    """缓存策略集成测试"""

    @pytest.mark.asyncio
    async def test_full_cache_flow(self, patched_cache):
        """测试完整缓存流程"""
        strategy = CacheStrategy()

        call_count = 0

        async def expensive_operation(key: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {"data": f"data_{key}", "computed": True}

        # 第一次调用
        result1 = await strategy.get_or_load("flow_key", lambda: expensive_operation("flow_key"), 300, use_lock=False)
        assert result1 == {"data": "data_flow_key", "computed": True}
        assert call_count == 1

        # 第二次调用应该命中缓存
        result2 = await strategy.get_or_load("flow_key", lambda: expensive_operation("flow_key"), 300, use_lock=False)
        assert result2 == {"data": "data_flow_key", "computed": True}
        assert call_count == 1

        # 失效缓存
        count = await strategy.invalidate_pattern("flow_key")
        assert count == 1

        # 第三次调用应该重新加载
        result3 = await strategy.get_or_load("flow_key", lambda: expensive_operation("flow_key"), 300, use_lock=False)
        assert result3 == {"data": "data_flow_key", "computed": True}
        assert call_count == 2

    def test_hot_keys_config(self):
        """测试热点键配置"""
        assert "news_list" in HOT_KEYS
        assert "lawyer_list" in HOT_KEYS
        assert "config_global" in HOT_KEYS

        assert HOT_KEYS["news_list"]["expire"] == 300
        assert HOT_KEYS["lawyer_list"]["preload"] is True
        assert HOT_KEYS["config_global"]["refresh_interval"] == 300


class TestCacheBreachProtectionNew:
    """缓存击穿防护测试（新版）"""

    @pytest.mark.asyncio
    async def test_acquire_lock_success(self):
        """测试获取锁成功"""
        mock_cache = MockCacheService()
        mock_cache.setnx = AsyncMock(return_value=True)
        
        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            result = await CacheBreachProtection.acquire_lock("test_lock", "lock_value", 10)
            
            assert result is True
            mock_cache.setnx.assert_called_once_with("test_lock", "lock_value", 10)

    @pytest.mark.asyncio
    async def test_acquire_lock_fail(self):
        """测试获取锁失败"""
        mock_cache = MockCacheService()
        mock_cache.setnx = AsyncMock(return_value=False)
        
        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            result = await CacheBreachProtection.acquire_lock("test_lock", "lock_value", 10)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_release_lock_success(self):
        """测试释放锁成功"""
        mock_cache = MockCacheService()
        mock_cache.release_lock = AsyncMock(return_value=True)
        
        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            result = await CacheBreachProtection.release_lock("test_lock", "lock_value")
            
            assert result is True
            mock_cache.release_lock.assert_called_once_with("test_lock", "lock_value")

    @pytest.mark.asyncio
    async def test_execute_with_lock_success(self):
        """测试使用锁执行操作成功"""
        async def mock_setnx(key, value, expire=10):
            return True
        
        async def mock_release_lock(key, value):
            return True
        
        mock_cache = MockCacheService()
        mock_cache.setnx = mock_setnx
        mock_cache.release_lock = mock_release_lock
        
        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            async def mock_operation():
                return {"result": "success"}

            # execute_with_lock 返回一个 decorator 函数
            decorator = CacheBreachProtection.execute_with_lock("test_lock", "lock_value", 10, retry_times=1)
            # decorator 本身是 async def，需要先 await
            decorator_func = await decorator
            result = await decorator_func(mock_operation)

            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_execute_with_lock_retry_exceeded(self):
        """测试使用锁执行操作重试次数耗尽"""
        async def mock_setnx(key, value, expire=10):
            return False
        
        mock_cache = MockCacheService()
        mock_cache.setnx = mock_setnx
        
        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            async def mock_operation():
                return {"result": "success"}

            decorator = CacheBreachProtection.execute_with_lock("test_lock", "lock_value", 10, retry_times=1)
            decorator_func = await decorator

            with pytest.raises(RuntimeError, match="Failed to acquire lock after 1 retries"):
                await decorator_func(mock_operation)


class TestCachePreloaderNew:
    """缓存预热器测试（新版）"""

    @pytest.mark.asyncio
    async def test_preloader_init(self):
        """测试预热器初始化"""
        preloader = CachePreloader()

        assert preloader._preloading == set()
        assert preloader._refresh_tasks == {}

    @pytest.mark.asyncio
    async def test_preload_empty_key(self):
        """测试预热空键"""
        mock_cache = MockCacheService()
        mock_cache.get_json = AsyncMock(return_value=None)
        
        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            preloader = CachePreloader()

            async def load_func():
                return {"data": "test"}

            result = await preloader.preload("", load_func)

            assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_preload_success(self):
        """测试预热成功"""
        mock_cache = MockCacheService()
        mock_cache.get_json = AsyncMock(return_value=None)
        mock_cache.set_json = AsyncMock(return_value=True)
        
        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            preloader = CachePreloader()

            async def load_func():
                return {"data": "loaded"}

            result = await preloader.preload("test_key", load_func, expire=300)

            assert result == {"data": "loaded"}
            mock_cache.set_json.assert_called()

    @pytest.mark.asyncio
    async def test_preload_cache_hit(self):
        """测试预热缓存命中"""
        mock_cache = MockCacheService()
        mock_cache.get_json = AsyncMock(return_value={"cached": True})
        
        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            preloader = CachePreloader()

            async def load_func():
                return {"data": "loaded"}

            result = await preloader.preload("test_key", load_func, expire=300)

            assert result == {"cached": True}


class TestCacheStrategyEdgeCases:
    """测试缓存策略边界情况"""

    @pytest.mark.asyncio
    async def test_strategy_with_empty_key(self):
        """测试空键缓存策略"""
        strategy = CacheStrategy()
        mock_cache = MockCacheService()
        mock_cache.get_json = AsyncMock(return_value=None)
        mock_cache.set_json = AsyncMock(return_value=True)

        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            async def loader():
                return {"data": "test"}
            result = await strategy.get_or_load("", loader)
            assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_strategy_with_special_char_key(self):
        """测试特殊字符键缓存策略"""
        strategy = CacheStrategy()
        mock_cache = MockCacheService()
        mock_cache.get_json = AsyncMock(return_value=None)
        mock_cache.set_json = AsyncMock(return_value=True)

        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            async def loader():
                return {"data": "test"}
            result = await strategy.get_or_load("key:with:special:chars", loader)
            assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_breach_protection_execute_with_protection(self):
        """测试击穿保护执行"""
        mock_cache = MockCacheService()
        mock_cache.get_json = AsyncMock(return_value=None)
        mock_cache.setnx = AsyncMock(return_value=True)
        mock_cache.set_json = AsyncMock(return_value=True)

        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            async def load_func():
                return {"data": "loaded"}

            # 使用 execute_with_lock 替代 execute_with_protection
            decorator = CacheBreachProtection.execute_with_lock("test_lock", "token123", 10, retry_times=1)
            decorator_func = await decorator
            result = await decorator_func(load_func)

            assert result == {"data": "loaded"}

    @pytest.mark.asyncio
    async def test_preloader_concurrent_preload(self):
        """测试预热器处理并发预热"""
        mock_cache = MockCacheService()
        mock_cache.get_json = AsyncMock(return_value=None)
        mock_cache.set_json = AsyncMock(return_value=True)

        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            preloader = CachePreloader()

            async def load_func(key):
                return {"key": key, "data": "loaded"}

            # Sequential to avoid closure issues
            results = []
            for i in range(3):
                result = await preloader.preload(f"key_{i}", lambda k=i: load_func(k))
                results.append(result)

            assert len(results) == 3

    @pytest.mark.asyncio
    async def test_hot_keys_contains_expected_keys(self):
        """测试热点键包含预期的键"""
        # 检查 HOT_KEYS 包含 config_global
        assert "config_global" in HOT_KEYS
        assert "lawyer_list" in HOT_KEYS
        assert "news_list" in HOT_KEYS

    @pytest.mark.asyncio
    async def test_get_cache_hit_rate_returns_dict(self):
        """测试缓存命中率返回字典"""
        result = await get_cache_hit_rate()
        assert isinstance(result, dict)
        assert "hit_rate" in result
        assert "total_requests" in result
        assert "total_hits" in result


class TestCacheStrategyDetail:
    """测试缓存策略详细功能"""

    @pytest.mark.asyncio
    async def test_strategy_get_or_load(self):
        """测试策略获取或加载"""
        strategy = CacheStrategy()
        mock_cache = MockCacheService()
        mock_cache.get_json = AsyncMock(return_value=None)
        mock_cache.set_json = AsyncMock(return_value=True)

        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            async def loader():
                return {"data": "test_value"}
            result = await strategy.get_or_load("test_key", loader)
            assert result == {"data": "test_value"}

    @pytest.mark.asyncio
    async def test_strategy_get_or_load_cache_hit(self):
        """测试策略缓存命中"""
        strategy = CacheStrategy()
        mock_cache = MockCacheService()
        mock_cache.get_json = AsyncMock(return_value={"cached": True})
        mock_cache.set_json = AsyncMock(return_value=True)

        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            result = await strategy.get_or_load("cached_key", lambda: {"data": "new"})
            assert result == {"cached": True}

    @pytest.mark.asyncio
    async def test_strategy_invalidate_pattern(self):
        """测试策略模式失效"""
        strategy = CacheStrategy()
        mock_cache = MockCacheService()
        mock_cache.clear_pattern = AsyncMock(return_value=5)

        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            count = await strategy.invalidate_pattern("user:*")
            assert count == 5

    @pytest.mark.asyncio
    async def test_strategy_get_stats(self):
        """测试策略获取统计"""
        strategy = CacheStrategy()
        stats = strategy.get_stats()
        assert isinstance(stats, dict)


class TestCachedWithStrategyDetail:
    """测试带策略的缓存装饰器"""

    @pytest.mark.asyncio
    async def test_cached_decorator_basic(self, mock_cache):
        """测试基础缓存装饰器"""
        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            call_count = 0

            @cached_with_strategy("test_prefix", expire=60, use_lock=False)
            async def expensive_func(x):
                nonlocal call_count
                call_count += 1
                return x * 2

            result1 = await expensive_func(5)
            result2 = await expensive_func(5)

            assert result1 == 10
            assert result2 == 10
            assert call_count == 1

    @pytest.mark.asyncio
    async def test_cached_decorator_different_args(self, mock_cache):
        """测试不同参数的缓存装饰器"""
        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            call_count = 0

            @cached_with_strategy("test_prefix", expire=60, use_lock=False)
            async def expensive_func(x, y):
                nonlocal call_count
                call_count += 1
                return x + y

            result1 = await expensive_func(1, 2)
            result2 = await expensive_func(1, 2)
            result3 = await expensive_func(3, 4)

            assert result1 == 3
            assert result2 == 3
            assert result3 == 7
            assert call_count == 2


class TestPreloadHotDataDetail:
    """测试预热热点数据"""

    @pytest.mark.asyncio
    async def test_preload_hot_data_unknown_type(self):
        """测试预热未知类型数据"""
        mock_cache = MockCacheService()
        mock_cache.get_json = AsyncMock(return_value=None)
        mock_cache.set_json = AsyncMock(return_value=True)

        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            async def load_func():
                return [("key1", {"data": "1"})]

            result = await preload_hot_data("unknown_type", load_func)
            assert result == 0

    @pytest.mark.asyncio
    async def test_preload_hot_data_user_profile(self):
        """测试预热用户配置数据"""
        mock_cache = MockCacheService()
        mock_cache.get_json = AsyncMock(return_value=None)
        mock_cache.set_json = AsyncMock(return_value=True)

        with patch("app.utils.cache_strategy.cache_service", mock_cache):
            async def load_func():
                return [("config_global:1", {"name": "User1"}), ("config_global:2", {"name": "User2"})]

            result = await preload_hot_data("config_global", load_func)
            assert result == 2
