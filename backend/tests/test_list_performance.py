import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.list_performance import (
    ListCacheManager,
    QueryOptimizer,
    ListPerformanceService,
    get_optimized_list
)

class TestListCacheManager:
    @pytest.fixture
    def manager(self):
        return ListCacheManager()

    def test_cache_key_generation(self, manager):
        key1 = manager.get_cache_key("news", 1, {"page": 1})
        key2 = manager.get_cache_key("news", 1, {"page": 1})
        key3 = manager.get_cache_key("news", 1, {"page": 2})
        key4 = manager.get_cache_key("forum", 1, {"page": 1})

        assert key1 == key2
        assert key1 != key3
        assert key1 != key4

    def test_set_and_get_cache(self, manager):
        key = "test_key"
        data = ["item1", "item2"]
        meta = {"info": "test"}

        manager.set(key, data, meta)
        
        cached_data = manager.get(key)
        assert cached_data == data

        # Test metadata stored?
        # The public .get() method returns "data" field of internal structure.
        # But we can check stats later.

    def test_cache_expiration(self, manager):
        key = "expire_key"
        manager._cache_ttl = 0.001 # very short ttl
        manager.set(key, ["data"], {})
        
        import time
        time.sleep(0.01)
        
        assert manager.get(key) is None

    def test_invalidate(self, manager):
        manager.set("news:1:abc", [], {})
        manager.set("news:2:def", [], {})
        manager.set("forum:1:xyz", [], {})

        count = manager.invalidate("news")
        assert count == 2
        assert manager.get("news:1:abc") is None
        assert manager.get("forum:1:xyz") is not None

    def test_get_stats(self, manager):
        key = "stat_key"
        manager.set(key, [], {})
        
        manager.get(key) # Hit 1
        
        stats = manager.get_stats()
        assert stats["total_keys"] == 1
        assert stats["hit_count"] == 1
        assert stats["hit_rate"] == 100.0


class TestQueryOptimizer:
    @pytest.fixture
    def optimizer(self):
        return QueryOptimizer()

    def test_optimize_query_defaults(self, optimizer):
        # Defaults
        params = {}
        opt = optimizer.optimize_query("news", params)
        assert opt["page"] == 1
        assert opt["page_size"] == 20

    def test_optimize_query_limits(self, optimizer):
        # Page size limit
        params = {"page_size": 1000}
        opt = optimizer.optimize_query("news", params)
        assert opt["page_size"] == 100

        # High page restriction
        params = {"page": 2, "page_size": 100}
        opt = optimizer.optimize_query("news", params)
        assert opt["page_size"] == 50

    def test_record_and_get_stats(self, optimizer):
        optimizer.record_query_time("news", 100.0, 10)
        optimizer.record_query_time("news", 200.0, 10)
        
        stats = optimizer.get_query_stats("news")
        assert stats["count"] == 2
        assert stats["avg_duration_ms"] == 150.0
        assert stats["max_duration_ms"] == 200.0

        # P95 check
        # With 2 items: [100, 200]. idx = int(2 * 0.95) = 1. p95 = durations[1] = 200
        assert stats["p95_duration_ms"] == 200.0


class TestListPerformanceService:
    @pytest.fixture
    def service(self):
        return ListPerformanceService()

    @pytest.mark.asyncio
    async def test_get_optimized_list_no_cache_then_cache(self, service):
        async def mock_fetch(params):
            return ["fetched_data"]

        # First call: No cache
        res1 = await service.get_optimized_list("news", 1, {}, mock_fetch)
        assert res1["from_cache"] is False
        assert res1["data"] == ["fetched_data"]
        
        # Second call: Should hit cache
        # Note: optimize_query adds defaults, so key should match if we pass empty {} again
        res2 = await service.get_optimized_list("news", 1, {}, mock_fetch)
        assert res2["from_cache"] is True
        assert res2["data"] == ["fetched_data"]

    @pytest.mark.asyncio
    async def test_invalidate_cache(self, service):
        async def mock_fetch(params):
            return []
            
        await service.get_optimized_list("news", 1, {}, mock_fetch)
        # Ensure it's cached
        stats_before = service._cache.get_stats()
        assert stats_before["total_keys"] > 0
        
        # Invalidate
        res = await service.invalidate_cache("news")
        assert res["invalidated"] >= 1
        
        stats_after = service._cache.get_stats()
        assert stats_after["total_keys"] == 0

    @pytest.mark.asyncio
    async def test_get_performance_stats(self, service):
        stats = await service.get_performance_stats()
        assert "cache" in stats
        assert "queries" in stats
        assert "news" in stats["queries"]

@pytest.mark.asyncio
async def test_global_helper_get_optimized_list():
    async def mock_fetch(params):
        return ["global_data"]
        
    res = await get_optimized_list("global_test", 999, {}, mock_fetch)
    assert res["data"] == ["global_data"]
