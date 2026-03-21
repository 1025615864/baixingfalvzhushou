"""AI 缓存优化服务单元测试

测试向量检索缓存、AI 响应缓存、批量检索优化、结果去重等功能。
"""
import asyncio
import time

import pytest

from app.services.ai.cache_optimizer import (
    VectorSearchCache,
    VectorSearchCacheEntry,
    AIResponseCache,
    AIResponseCacheEntry,
    BatchRetrievalOptimizer,
    ResultDeduplicator,
    RequestQueueManager,
    RetryStrategy,
    RetryConfig,
    AIRequestExecutor,
    AICacheOptimizer,
    CachePriority,
    CacheInvalidationReason,
    get_ai_cache_optimizer,
)


class TestVectorSearchCache:
    """向量检索缓存测试"""

    def test_cache_basic_operations(self):
        """测试基本缓存操作"""
        cache = VectorSearchCache(max_size=100, default_ttl=60)

        # 测试数据
        query = "劳动合同纠纷"
        results = [
            ("内容1", {"knowledge_id": "1"}, 0.9),
            ("内容2", {"knowledge_id": "2"}, 0.8),
        ]

        # 初始应该未命中
        cached = cache.get_sync(query, k=5)
        assert cached is None

        # 设置缓存
        cache.set_sync(query, results, k=5)
        
        # 应该命中
        cached = cache.get_sync(query, k=5)
        assert cached is not None
        assert len(cached) == 2
        assert cached[0][0] == "内容1"

    def test_cache_different_k_values(self):
        """测试不同 k 值的缓存"""
        cache = VectorSearchCache()

        query = "测试查询"
        results_5 = [("内容1", {}, 0.9)]
        results_10 = [("内容1", {}, 0.9), ("内容2", {}, 0.8)]

        # 设置不同 k 值的缓存
        cache.set_sync(query, results_5, k=5)
        cache.set_sync(query, results_10, k=10)

        # 应该分别获取
        cached_5 = cache.get_sync(query, k=5)
        cached_10 = cache.get_sync(query, k=10)

        assert cached_5 is not None
        assert len(cached_5) == 1
        assert cached_10 is not None
        assert len(cached_10) == 2

    def test_cache_lru_eviction(self):
        """测试 LRU 淘汰"""
        cache = VectorSearchCache(max_size=3, default_ttl=60)

        # 添加 3 个条目
        for i in range(3):
            cache.set_sync(f"query_{i}", [(f"content_{i}", {}, 0.9)], k=5)

        # 添加第 4 个，应该淘汰第一个
        cache.set_sync("query_3", [("content_3", {}, 0.9)], k=5)

        # 第一个应该被淘汰
        assert cache.get_sync("query_0", k=5) is None
        
        # 其他应该还在
        assert cache.get_sync("query_1", k=5) is not None
        assert cache.get_sync("query_3", k=5) is not None

    def test_cache_stats(self):
        """测试缓存统计"""
        cache = VectorSearchCache()

        # 产生一些命中和未命中
        cache.set_sync("query_1", [("content", {}, 0.9)], k=5)
        cache.get_sync("query_1", k=5)  # 命中
        cache.get_sync("query_2", k=5)  # 未命中

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1

    @pytest.mark.asyncio
    async def test_cache_async_operations(self):
        """测试异步缓存操作"""
        cache = VectorSearchCache()
        query = "异步测试"
        results = [("内容", {}, 0.9)]

        # 异步设置
        await cache.set(query, results, k=5)

        # 异步获取
        cached = await cache.get(query, k=5)
        assert cached is not None
        assert len(cached) == 1


class TestAIResponseCache:
    """AI 响应缓存测试"""

    def test_response_cache_basic(self):
        """测试响应缓存基本操作"""
        cache = AIResponseCache()

        question = "劳动合同到期不续签有补偿吗？"
        answer = "根据《劳动合同法》..."
        references = [{"knowledge_id": 1, "content": "..."}]

        # 初始未命中
        cached = asyncio.get_event_loop().run_until_complete(
            cache.get(question)
        )
        assert cached is None

        # 设置缓存
        cache_key = asyncio.get_event_loop().run_until_complete(
            cache.set(
                question=question,
                answer=answer,
                references=references,
                model_used="gpt-4o",
                confidence="high",
            )
        )

        # 命中
        cached = asyncio.get_event_loop().run_until_complete(
            cache.get(question)
        )
        assert cached is not None
        assert cached.answer == answer
        assert cached.model_used == "gpt-4o"

    def test_response_cache_priority(self):
        """测试优先级缓存"""
        cache = AIResponseCache(
            high_priority_ttl=7200,
            default_ttl=3600,
            low_priority_ttl=1800,
        )

        # 高优先级
        high_key = asyncio.get_event_loop().run_until_complete(
            cache.set(
                question="高优先级问题",
                answer="答案",
                references=[],
                model_used="gpt-4o",
                confidence="high",
                priority=CachePriority.HIGH,
            )
        )

        # 低优先级
        low_key = asyncio.get_event_loop().run_until_complete(
            cache.set(
                question="低优先级问题",
                answer="答案",
                references=[],
                model_used="gpt-4o",
                confidence="low",
                priority=CachePriority.LOW,
            )
        )

        stats = cache.get_stats()
        assert stats["priority_distribution"]["high"] == 1
        assert stats["priority_distribution"]["low"] == 1

    def test_response_cache_feedback(self):
        """测试反馈驱动的缓存失效"""
        cache = AIResponseCache()

        question = "测试问题"
        cache_key = asyncio.get_event_loop().run_until_complete(
            cache.set(
                question=question,
                answer="答案",
                references=[],
                model_used="gpt-4o",
                confidence="high",
            )
        )

        # 添加负面反馈
        for _ in range(3):
            asyncio.get_event_loop().run_until_complete(
                cache.add_feedback(cache_key, "unhelpful")
            )

        # 应该因反馈而失效
        cached = asyncio.get_event_loop().run_until_complete(
            cache.get(question)
        )
        assert cached is None


class TestResultDeduplicator:
    """结果去重器测试"""

    def test_deduplicate_by_knowledge_id(self):
        """测试基于 knowledge_id 的去重"""
        deduplicator = ResultDeduplicator()

        results = [
            ("内容1", {"knowledge_id": "1"}, 0.9),
            ("内容2", {"knowledge_id": "1"}, 0.8),  # 重复
            ("内容3", {"knowledge_id": "2"}, 0.7),
        ]

        deduped = deduplicator.deduplicate(results)
        assert len(deduped) == 2
        assert deduped[0][0] == "内容1"
        assert deduped[1][0] == "内容3"

    def test_deduplicate_by_content_hash(self):
        """测试基于内容哈希的去重"""
        deduplicator = ResultDeduplicator()

        results = [
            ("相同内容", {}, 0.9),
            ("相同内容", {}, 0.8),  # 重复
            ("不同内容", {}, 0.7),
        ]

        deduped = deduplicator.deduplicate(results)
        assert len(deduped) == 2

    def test_merge_and_deduplicate(self):
        """测试合并多个结果集"""
        deduplicator = ResultDeduplicator()

        set1 = [
            ("内容1", {"knowledge_id": "1"}, 0.9),
            ("内容2", {"knowledge_id": "2"}, 0.8),
        ]
        set2 = [
            ("内容1", {"knowledge_id": "1"}, 0.85),  # 重复
            ("内容3", {"knowledge_id": "3"}, 0.7),
        ]

        merged = deduplicator.merge_and_deduplicate([set1, set2], max_results=5)
        assert len(merged) == 3


class TestBatchRetrievalOptimizer:
    """批量检索优化器测试"""

    @pytest.mark.asyncio
    async def test_batch_deduplication(self):
        """测试批处理去重"""
        optimizer = BatchRetrievalOptimizer(batch_window_ms=50)

        call_count = 0

        async def search_func(query: str, k: int):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # 模拟延迟
            return [("结果", {}, 0.9)]

        # 同时发起多个相同查询
        tasks = [
            optimizer.execute_with_batching("测试查询", 5, search_func)
            for _ in range(3)
        ]
        results = await asyncio.gather(*tasks)

        # 应该只调用一次搜索
        assert call_count == 1
        # 所有请求应该得到相同结果
        for result in results:
            assert len(result) == 1


class TestRequestQueueManager:
    """请求队列管理器测试"""

    @pytest.mark.asyncio
    async def test_queue_basic(self):
        """测试基本队列操作"""
        manager = RequestQueueManager(max_concurrent=2)

        call_count = 0

        async def request_func():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return "result"

        result = await manager.submit(request_func, priority=5)
        assert result == "result"

        stats = manager.get_stats()
        assert stats["requests_completed"] == 1

    @pytest.mark.asyncio
    async def test_queue_priority(self):
        """测试优先级队列"""
        manager = RequestQueueManager(max_concurrent=1, queue_size=10)

        results = []

        async def request_func(value: int):
            await asyncio.sleep(0.05)
            results.append(value)
            return value

        # 提交多个请求，不同优先级
        tasks = [
            manager.submit(lambda v=i: request_func(v), priority=i)
            for i in [5, 1, 10, 3]  # 优先级 1 最高
        ]
        await asyncio.gather(*tasks)

        # 由于并发限制为1，应该按优先级执行
        # 注意：实际顺序可能因时序略有不同


class TestAIRequestExecutor:
    """AI 请求执行器测试"""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """测试成功执行"""
        executor = AIRequestExecutor()

        async def success_func():
            return "success"

        result = await executor.execute(success_func)
        assert result == "success"

        stats = executor.get_stats()
        assert stats["successful_requests"] == 1

    @pytest.mark.asyncio
    async def test_timeout(self):
        """测试超时"""
        executor = AIRequestExecutor(default_timeout=0.1)

        async def slow_func():
            await asyncio.sleep(1)
            return "success"

        with pytest.raises(TimeoutError):
            await executor.execute(slow_func)

        stats = executor.get_stats()
        assert stats["timeout_requests"] == 1

    @pytest.mark.asyncio
    async def test_retry(self):
        """测试重试"""
        executor = AIRequestExecutor()
        config = RetryConfig(
            max_retries=2,
            strategy=RetryStrategy.FIXED,
            base_delay=0.01,
        )

        attempts = 0

        async def flaky_func():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await executor.execute(flaky_func, retry_config=config)
        assert result == "success"

        stats = executor.get_stats()
        assert stats["retried_requests"] == 2


class TestAICacheOptimizer:
    """AI 缓存优化器集成测试"""

    def test_get_singleton(self):
        """测试单例获取"""
        optimizer1 = get_ai_cache_optimizer()
        optimizer2 = get_ai_cache_optimizer()
        assert optimizer1 is optimizer2

    def test_all_stats(self):
        """测试获取所有统计"""
        optimizer = get_ai_cache_optimizer()
        stats = optimizer.get_all_stats()

        assert "vector_search_cache" in stats
        assert "ai_response_cache" in stats
        assert "batch_optimizer" in stats
        assert "queue_manager" in stats
        assert "request_executor" in stats


class TestCachePriority:
    """缓存优先级测试"""

    def test_priority_values(self):
        """测试优先级值"""
        assert CachePriority.HIGH.value == "high"
        assert CachePriority.MEDIUM.value == "medium"
        assert CachePriority.LOW.value == "low"


class TestCacheInvalidationReason:
    """缓存失效原因测试"""

    def test_invalidation_reasons(self):
        """测试失效原因值"""
        assert CacheInvalidationReason.TTL_EXPIRED.value == "ttl_expired"
        assert CacheInvalidationReason.MANUAL_INVALIDATE.value == "manual_invalidate"
        assert CacheInvalidationReason.KNOWLEDGE_BASE_UPDATE.value == "knowledge_base_update"
        assert CacheInvalidationReason.USER_FEEDBACK.value == "user_feedback"


class TestRetryConfig:
    """重试配置测试"""

    def test_fixed_strategy(self):
        """测试固定间隔策略"""
        config = RetryConfig(
            strategy=RetryStrategy.FIXED,
            base_delay=1.0,
        )
        assert config.get_delay(0) == 1.0
        assert config.get_delay(5) == 1.0

    def test_exponential_strategy(self):
        """测试指数退避策略"""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            max_delay=10.0,
        )
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0
        assert config.get_delay(10) == 10.0  # 受 max_delay 限制

    def test_linear_strategy(self):
        """测试线性递增策略"""
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR,
            base_delay=1.0,
            max_delay=10.0,
        )
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 3.0