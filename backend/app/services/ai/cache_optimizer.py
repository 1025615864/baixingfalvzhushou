"""AI 缓存优化服务

提供向量检索缓存、AI 响应缓存、批量检索优化、结果去重、
请求队列管理、超时和重试机制等功能。
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Generic, TypeVar

from ..multi_level_cache import MultiLevelCache, CacheStats, cache_manager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CachePriority(Enum):
    """缓存优先级"""
    HIGH = "high"      # 高优先级：常见问题、热点数据
    MEDIUM = "medium"  # 中优先级：普通查询
    LOW = "low"        # 低优先级：冷数据


class CacheInvalidationReason(Enum):
    """缓存失效原因"""
    TTL_EXPIRED = "ttl_expired"
    MANUAL_INVALIDATE = "manual_invalidate"
    KNOWLEDGE_BASE_UPDATE = "knowledge_base_update"
    MODEL_CONFIG_CHANGE = "model_config_change"
    USER_FEEDBACK = "user_feedback"
    LRU_EVICTION = "lru_eviction"


@dataclass
class VectorSearchCacheEntry:
    """向量检索缓存条目"""
    query_hash: str
    query_text: str
    results: list[tuple[str, dict[str, Any], float]]
    created_at: float
    expires_at: float
    hit_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > self.expires_at
    
    def touch(self) -> None:
        """更新访问信息"""
        self.hit_count += 1
        self.last_accessed = time.time()


@dataclass
class AIResponseCacheEntry:
    """AI 响应缓存条目"""
    cache_key: str
    question: str
    answer: str
    references: list[dict[str, Any]]
    model_used: str | None
    confidence: str
    created_at: float
    expires_at: float
    priority: CachePriority
    hit_count: int = 0
    user_feedback: list[str] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > self.expires_at
    
    def add_feedback(self, feedback: str) -> None:
        """添加用户反馈"""
        self.user_feedback.append(feedback)
    
    def should_invalidate(self) -> bool:
        """判断是否应该失效（基于负反馈）"""
        if len(self.user_feedback) < 3:
            return False
        negative_count = sum(1 for f in self.user_feedback if f in ["bad", "unhelpful", "incorrect"])
        return negative_count / len(self.user_feedback) > 0.5


class VectorSearchCache:
    """向量检索缓存
    
    为知识库向量检索结果提供缓存，避免重复的向量计算。
    """
    
    def __init__(
        self,
        max_size: int = 500,
        default_ttl: int = 600,  # 10 分钟
        similarity_threshold: float = 0.95,
    ):
        self._cache: OrderedDict[str, VectorSearchCacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._similarity_threshold = similarity_threshold
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
    
    def _hash_query(self, query: str, k: int = 5) -> str:
        """生成查询哈希"""
        normalized_query = " ".join(query.lower().strip().split())
        content = f"{normalized_query}:{k}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get(
        self,
        query: str,
        k: int = 5,
    ) -> list[tuple[str, dict[str, Any], float]] | None:
        """获取缓存的检索结果"""
        cache_key = self._hash_query(query, k)
        
        async with self._lock:
            entry = self._cache.get(cache_key)
            if entry is None:
                self._stats.misses += 1
                return None
            
            if entry.is_expired():
                del self._cache[cache_key]
                self._stats.evictions += 1
                self._stats.misses += 1
                logger.debug(f"Vector search cache expired: {cache_key}")
                return None
            
            entry.touch()
            self._cache.move_to_end(cache_key)
            self._stats.hits += 1
            logger.debug(f"Vector search cache hit: {cache_key}, hits={entry.hit_count}")
            return entry.results
    
    async def set(
        self,
        query: str,
        results: list[tuple[str, dict[str, Any], float]],
        k: int = 5,
        ttl: int | None = None,
    ) -> None:
        """设置检索结果缓存"""
        cache_key = self._hash_query(query, k)
        expires_at = time.time() + (ttl or self._default_ttl)
        
        async with self._lock:
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
            elif len(self._cache) >= self._max_size:
                # LRU 淘汰
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats.evictions += 1
                logger.debug(f"Vector search cache LRU evicted: {oldest_key}")
            
            entry = VectorSearchCacheEntry(
                query_hash=cache_key,
                query_text=query,
                results=results,
                created_at=time.time(),
                expires_at=expires_at,
            )
            self._cache[cache_key] = entry
            self._stats.writes += 1
            logger.debug(f"Vector search cache set: {cache_key}")
    
    async def invalidate(self, query: str, k: int = 5) -> bool:
        """使特定查询的缓存失效"""
        cache_key = self._hash_query(query, k)
        async with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.debug(f"Vector search cache invalidated: {cache_key}")
                return True
            return False
    
    async def invalidate_all(self) -> int:
        """使所有缓存失效"""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Vector search cache cleared: {count} entries")
            return count
    
    def get_sync(
        self,
        query: str,
        k: int = 5,
    ) -> list[tuple[str, dict[str, Any], float]] | None:
        """同步获取缓存的检索结果（用于非异步上下文）"""
        cache_key = self._hash_query(query, k)
        
        entry = self._cache.get(cache_key)
        if entry is None:
            self._stats.misses += 1
            return None
        
        if entry.is_expired():
            del self._cache[cache_key]
            self._stats.evictions += 1
            self._stats.misses += 1
            logger.debug(f"Vector search cache expired: {cache_key}")
            return None
        
        entry.touch()
        # 手动移动到末尾（LRU）
        self._cache.move_to_end(cache_key)
        self._stats.hits += 1
        logger.debug(f"Vector search cache hit: {cache_key}, hits={entry.hit_count}")
        return entry.results
    
    def set_sync(
        self,
        query: str,
        results: list[tuple[str, dict[str, Any], float]],
        k: int = 5,
        ttl: int | None = None,
    ) -> None:
        """同步设置检索结果缓存（用于非异步上下文）"""
        cache_key = self._hash_query(query, k)
        expires_at = time.time() + (ttl or self._default_ttl)
        
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
        elif len(self._cache) >= self._max_size:
            # LRU 淘汰
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats.evictions += 1
            logger.debug(f"Vector search cache LRU evicted: {oldest_key}")
        
        entry = VectorSearchCacheEntry(
            query_hash=cache_key,
            query_text=query,
            results=results,
            created_at=time.time(),
            expires_at=expires_at,
        )
        self._cache[cache_key] = entry
        self._stats.writes += 1
        logger.debug(f"Vector search cache set: {cache_key}")
    
    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return {
            "cache_type": "vector_search",
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "hit_rate_percent": round(
                self._stats.hits / (self._stats.hits + self._stats.misses) * 100
                if (self._stats.hits + self._stats.misses) > 0 else 0, 2
            ),
            "evictions": self._stats.evictions,
            "writes": self._stats.writes,
        }


class AIResponseCache:
    """AI 响应缓存
    
    为 AI 生成的内容提供缓存，支持智能失效机制。
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,  # 1 小时
        high_priority_ttl: int = 7200,  # 2 小时
        low_priority_ttl: int = 1800,  # 30 分钟
    ):
        self._cache: OrderedDict[str, AIResponseCacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._high_priority_ttl = high_priority_ttl
        self._low_priority_ttl = low_priority_ttl
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
        self._invalidation_callbacks: list[Callable[[str, CacheInvalidationReason], None]] = []
    
    def _get_ttl_for_priority(self, priority: CachePriority) -> int:
        """根据优先级获取 TTL"""
        if priority == CachePriority.HIGH:
            return self._high_priority_ttl
        elif priority == CachePriority.LOW:
            return self._low_priority_ttl
        return self._default_ttl
    
    def _hash_question(self, question: str, context_hash: str = "") -> str:
        """生成问题哈希"""
        normalized = " ".join(question.lower().strip().split())
        content = f"{normalized}:{context_hash}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def register_invalidation_callback(
        self,
        callback: Callable[[str, CacheInvalidationReason], None],
    ) -> None:
        """注册缓存失效回调"""
        self._invalidation_callbacks.append(callback)
    
    def _notify_invalidation(
        self,
        cache_key: str,
        reason: CacheInvalidationReason,
    ) -> None:
        """通知缓存失效"""
        for callback in self._invalidation_callbacks:
            try:
                callback(cache_key, reason)
            except Exception as e:
                logger.warning(f"Invalidation callback error: {e}")
    
    async def get(
        self,
        question: str,
        context_hash: str = "",
    ) -> AIResponseCacheEntry | None:
        """获取缓存的 AI 响应"""
        cache_key = self._hash_question(question, context_hash)
        
        async with self._lock:
            entry = self._cache.get(cache_key)
            if entry is None:
                self._stats.misses += 1
                return None
            
            if entry.is_expired():
                del self._cache[cache_key]
                self._stats.evictions += 1
                self._stats.misses += 1
                self._notify_invalidation(cache_key, CacheInvalidationReason.TTL_EXPIRED)
                logger.debug(f"AI response cache expired: {cache_key}")
                return None
            
            # 检查是否应该因负反馈而失效
            if entry.should_invalidate():
                del self._cache[cache_key]
                self._stats.evictions += 1
                self._stats.misses += 1
                self._notify_invalidation(cache_key, CacheInvalidationReason.USER_FEEDBACK)
                logger.debug(f"AI response cache invalidated by feedback: {cache_key}")
                return None
            
            entry.hit_count += 1
            self._cache.move_to_end(cache_key)
            self._stats.hits += 1
            logger.debug(f"AI response cache hit: {cache_key}, hits={entry.hit_count}")
            return entry
    
    async def set(
        self,
        question: str,
        answer: str,
        references: list[dict[str, Any]],
        model_used: str | None,
        confidence: str,
        context_hash: str = "",
        priority: CachePriority = CachePriority.MEDIUM,
        ttl: int | None = None,
    ) -> str:
        """设置 AI 响应缓存"""
        cache_key = self._hash_question(question, context_hash)
        effective_ttl = ttl or self._get_ttl_for_priority(priority)
        expires_at = time.time() + effective_ttl
        
        async with self._lock:
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
            elif len(self._cache) >= self._max_size:
                # 优先淘汰低优先级的条目
                low_priority_key = None
                for key, entry in self._cache.items():
                    if entry.priority == CachePriority.LOW:
                        low_priority_key = key
                        break
                
                if low_priority_key:
                    del self._cache[low_priority_key]
                else:
                    # LRU 淘汰
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                self._stats.evictions += 1
            
            entry = AIResponseCacheEntry(
                cache_key=cache_key,
                question=question,
                answer=answer,
                references=references,
                model_used=model_used,
                confidence=confidence,
                created_at=time.time(),
                expires_at=expires_at,
                priority=priority,
            )
            self._cache[cache_key] = entry
            self._stats.writes += 1
            logger.debug(f"AI response cache set: {cache_key}, priority={priority.value}")
            return cache_key
    
    async def add_feedback(
        self,
        cache_key: str,
        feedback: str,
    ) -> bool:
        """添加用户反馈"""
        async with self._lock:
            entry = self._cache.get(cache_key)
            if entry is None:
                return False
            
            entry.add_feedback(feedback)
            
            # 检查是否需要因反馈失效
            if entry.should_invalidate():
                del self._cache[cache_key]
                self._stats.evictions += 1
                self._notify_invalidation(cache_key, CacheInvalidationReason.USER_FEEDBACK)
                logger.info(f"AI response invalidated by negative feedback: {cache_key}")
            
            return True
    
    async def invalidate_by_pattern(
        self,
        pattern: str,
        reason: CacheInvalidationReason = CacheInvalidationReason.MANUAL_INVALIDATE,
    ) -> int:
        """按模式使缓存失效"""
        import fnmatch
        count = 0
        async with self._lock:
            keys_to_delete = [
                k for k in self._cache.keys()
                if fnmatch.fnmatch(k, pattern)
            ]
            for key in keys_to_delete:
                del self._cache[key]
                self._notify_invalidation(key, reason)
                count += 1
        logger.info(f"AI response cache invalidated {count} entries by pattern: {pattern}")
        return count
    
    async def invalidate_all(
        self,
        reason: CacheInvalidationReason = CacheInvalidationReason.MANUAL_INVALIDATE,
    ) -> int:
        """使所有缓存失效"""
        async with self._lock:
            count = len(self._cache)
            for key in list(self._cache.keys()):
                self._notify_invalidation(key, reason)
            self._cache.clear()
        logger.info(f"AI response cache cleared: {count} entries")
        return count
    
    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        priority_counts = {p.value: 0 for p in CachePriority}
        for entry in self._cache.values():
            priority_counts[entry.priority.value] += 1
        
        return {
            "cache_type": "ai_response",
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "hit_rate_percent": round(
                self._stats.hits / (self._stats.hits + self._stats.misses) * 100
                if (self._stats.hits + self._stats.misses) > 0 else 0, 2
            ),
            "evictions": self._stats.evictions,
            "writes": self._stats.writes,
            "priority_distribution": priority_counts,
        }


class BatchRetrievalOptimizer:
    """批量检索优化器
    
    合并多个相似的检索请求，减少重复计算。
    """
    
    def __init__(
        self,
        batch_window_ms: int = 100,  # 批处理窗口（毫秒）
        max_batch_size: int = 10,
    ):
        self._batch_window_ms = batch_window_ms
        self._max_batch_size = max_batch_size
        self._pending_requests: dict[str, list[tuple[asyncio.Future, str, int]]] = {}
        self._lock = asyncio.Lock()
        self._stats = {
            "batches_processed": 0,
            "requests_deduplicated": 0,
            "total_requests": 0,
        }
    
    async def execute_with_batching(
        self,
        query: str,
        k: int,
        search_func: Callable[[str, int], Any],
    ) -> list[tuple[str, dict[str, Any], float]]:
        """使用批处理执行检索"""
        self._stats["total_requests"] += 1
        
        # 生成批处理键
        batch_key = self._generate_batch_key(query, k)
        
        async with self._lock:
            if batch_key in self._pending_requests:
                # 添加到现有批次
                future: asyncio.Future = asyncio.get_event_loop().create_future()
                self._pending_requests[batch_key].append((future, query, k))
                self._stats["requests_deduplicated"] += 1
                logger.debug(f"Request added to existing batch: {batch_key}")
            else:
                # 创建新批次
                future = asyncio.get_event_loop().create_future()
                self._pending_requests[batch_key] = [(future, query, k)]
                logger.debug(f"New batch created: {batch_key}")
                
                # 启动批处理任务
                asyncio.create_task(self._process_batch(batch_key, search_func))
        
        return await future
    
    def _generate_batch_key(self, query: str, k: int) -> str:
        """生成批处理键"""
        normalized = " ".join(query.lower().strip().split())
        return f"{hashlib.md5(normalized.encode()).hexdigest()}:{k}"
    
    async def _process_batch(
        self,
        batch_key: str,
        search_func: Callable[[str, int], Any],
    ) -> None:
        """处理批次请求"""
        # 等待批处理窗口
        await asyncio.sleep(self._batch_window_ms / 1000.0)
        
        async with self._lock:
            requests = self._pending_requests.pop(batch_key, [])
        
        if not requests:
            return
        
        self._stats["batches_processed"] += 1
        logger.debug(f"Processing batch {batch_key} with {len(requests)} requests")
        
        try:
            # 执行一次检索
            _, query, k = requests[0]
            results = await search_func(query, k)
            
            # 向所有等待的请求返回结果
            for future, _, _ in requests:
                if not future.done():
                    future.set_result(results)
                    
        except Exception as e:
            # 向所有等待的请求返回错误
            for future, _, _ in requests:
                if not future.done():
                    future.set_exception(e)
            logger.error(f"Batch processing error: {e}")
    
    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "optimizer_type": "batch_retrieval",
            **self._stats,
            "deduplication_rate_percent": round(
                self._stats["requests_deduplicated"] / self._stats["total_requests"] * 100
                if self._stats["total_requests"] > 0 else 0, 2
            ),
        }


class ResultDeduplicator:
    """检索结果去重器
    
    对检索结果进行去重，避免重复内容。
    """
    
    def __init__(
        self,
        content_similarity_threshold: float = 0.9,
    ):
        self._content_similarity_threshold = content_similarity_threshold
    
    def deduplicate(
        self,
        results: list[tuple[str, dict[str, Any], float]],
    ) -> list[tuple[str, dict[str, Any], float]]:
        """对结果进行去重"""
        if not results:
            return results
        
        deduplicated: list[tuple[str, dict[str, Any], float]] = []
        seen_content_hashes: set[str] = set()
        seen_knowledge_ids: set[int] = set()
        
        for content, metadata, score in results:
            # 基于 knowledge_id 去重
            knowledge_id = metadata.get("knowledge_id")
            if knowledge_id is not None:
                kid = int(knowledge_id) if str(knowledge_id).isdigit() else None
                if kid is not None and kid in seen_knowledge_ids:
                    logger.debug(f"Duplicate result filtered by knowledge_id: {kid}")
                    continue
                if kid is not None:
                    seen_knowledge_ids.add(kid)
            
            # 基于内容哈希去重
            content_hash = hashlib.md5(content.strip().encode()).hexdigest()
            if content_hash in seen_content_hashes:
                logger.debug(f"Duplicate result filtered by content hash")
                continue
            seen_content_hashes.add(content_hash)
            
            deduplicated.append((content, metadata, score))
        
        logger.debug(f"Deduplicated results: {len(results)} -> {len(deduplicated)}")
        return deduplicated
    
    def merge_and_deduplicate(
        self,
        result_sets: list[list[tuple[str, dict[str, Any], float]]],
        max_results: int = 5,
    ) -> list[tuple[str, dict[str, Any], float]]:
        """合并多个结果集并去重"""
        all_results: list[tuple[str, dict[str, Any], float]] = []
        
        for results in result_sets:
            all_results.extend(results)
        
        # 按分数排序
        all_results.sort(key=lambda x: x[2], reverse=True)
        
        # 去重
        deduplicated = self.deduplicate(all_results)
        
        # 限制结果数量
        return deduplicated[:max_results]


class RequestQueueManager:
    """请求队列管理器
    
    管理 AI 模型调用请求的队列，支持优先级和并发控制。
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        queue_size: int = 100,
        request_timeout: float = 60.0,
    ):
        self._max_concurrent = max_concurrent
        self._queue_size = queue_size
        self._request_timeout = request_timeout
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=queue_size)
        self._active_requests = 0
        self._lock = asyncio.Lock()
        self._stats = {
            "requests_queued": 0,
            "requests_completed": 0,
            "requests_timeout": 0,
            "queue_full_rejects": 0,
        }
    
    async def submit(
        self,
        request_func: Callable[[], Any],
        priority: int = 5,  # 1=最高, 10=最低
        timeout: float | None = None,
    ) -> Any:
        """提交请求到队列"""
        effective_timeout = timeout or self._request_timeout
        
        # 检查队列是否已满
        if self._queue.full():
            self._stats["queue_full_rejects"] += 1
            raise RuntimeError("Request queue is full")
        
        self._stats["requests_queued"] += 1
        
        # 创建请求项
        request_id = time.time_ns()
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        queue_item = (priority, request_id, request_func, future, effective_timeout)
        
        await self._queue.put(queue_item)
        
        # 启动队列处理器（如果需要）
        asyncio.create_task(self._process_queue())
        
        try:
            result = await asyncio.wait_for(future, timeout=effective_timeout)
            self._stats["requests_completed"] += 1
            return result
        except asyncio.TimeoutError:
            self._stats["requests_timeout"] += 1
            raise TimeoutError(f"Request timed out after {effective_timeout}s")
    
    async def _process_queue(self) -> None:
        """处理队列中的请求"""
        async with self._lock:
            if self._active_requests >= self._max_concurrent:
                return
            self._active_requests += 1
        
        try:
            while True:
                try:
                    # 非阻塞获取
                    priority, request_id, request_func, future, timeout = \
                        self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                
                asyncio.create_task(
                    self._execute_request(request_func, future, timeout)
                )
        finally:
            async with self._lock:
                self._active_requests -= 1
    
    async def _execute_request(
        self,
        request_func: Callable[[], Any],
        future: asyncio.Future,
        timeout: float,
    ) -> None:
        """执行单个请求"""
        try:
            result = await asyncio.wait_for(request_func(), timeout=timeout)
            if not future.done():
                future.set_result(result)
        except Exception as e:
            if not future.done():
                future.set_exception(e)
    
    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "queue_type": "request_queue",
            "max_concurrent": self._max_concurrent,
            "queue_size": self._queue_size,
            "current_queue_length": self._queue.qsize(),
            "active_requests": self._active_requests,
            **self._stats,
        }


class RetryStrategy(Enum):
    """重试策略"""
    FIXED = "fixed"           # 固定间隔
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"         # 线性递增


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0
    max_delay: float = 30.0
    retryable_exceptions: tuple = (TimeoutError, ConnectionError, Exception)
    
    def get_delay(self, attempt: int) -> float:
        """获取重试延迟"""
        if self.strategy == RetryStrategy.FIXED:
            return min(self.base_delay, self.max_delay)
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** attempt)
            return min(delay, self.max_delay)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
            return min(delay, self.max_delay)
        return self.base_delay


class AIRequestExecutor:
    """AI 请求执行器
    
    提供超时和重试机制的 AI 请求执行。
    """
    
    def __init__(
        self,
        default_timeout: float = 30.0,
        default_retry_config: RetryConfig | None = None,
    ):
        self._default_timeout = default_timeout
        self._default_retry_config = default_retry_config or RetryConfig()
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retried_requests": 0,
            "timeout_requests": 0,
        }
    
    async def execute(
        self,
        request_func: Callable[[], Any],
        timeout: float | None = None,
        retry_config: RetryConfig | None = None,
    ) -> Any:
        """执行请求，支持超时和重试"""
        effective_timeout = timeout or self._default_timeout
        config = retry_config or self._default_retry_config
        
        self._stats["total_requests"] += 1
        last_exception: Exception | None = None
        
        for attempt in range(config.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    request_func(),
                    timeout=effective_timeout,
                )
                self._stats["successful_requests"] += 1
                return result
                
            except asyncio.TimeoutError as e:
                self._stats["timeout_requests"] += 1
                last_exception = TimeoutError(
                    f"Request timed out after {effective_timeout}s"
                )
                logger.warning(f"Request timeout (attempt {attempt + 1}/{config.max_retries + 1})")
                
            except config.retryable_exceptions as e:
                last_exception = e
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{config.max_retries + 1}): {e}"
                )
            
            # 如果还有重试机会，等待后重试
            if attempt < config.max_retries:
                self._stats["retried_requests"] += 1
                delay = config.get_delay(attempt)
                logger.debug(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        self._stats["failed_requests"] += 1
        raise last_exception or RuntimeError("Request failed")
    
    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "executor_type": "ai_request",
            **self._stats,
            "success_rate_percent": round(
                self._stats["successful_requests"] / self._stats["total_requests"] * 100
                if self._stats["total_requests"] > 0 else 0, 2
            ),
        }


class AICacheOptimizer:
    """AI 缓存优化器
    
    整合所有 AI 缓存和优化功能的统一入口。
    """
    
    def __init__(
        self,
        vector_cache_size: int = 500,
        response_cache_size: int = 1000,
        max_concurrent_requests: int = 5,
    ):
        # 初始化各组件
        self.vector_search_cache = VectorSearchCache(max_size=vector_cache_size)
        self.response_cache = AIResponseCache(max_size=response_cache_size)
        self.batch_optimizer = BatchRetrievalOptimizer()
        self.deduplicator = ResultDeduplicator()
        self.queue_manager = RequestQueueManager(max_concurrent=max_concurrent_requests)
        self.request_executor = AIRequestExecutor()
        
        # 多级缓存（用于其他 AI 相关数据）
        self._multi_level_cache = cache_manager.get_cache(
            "ai_optimizer",
            l1_max_size=500,
            l1_default_ttl=120,
            l2_default_ttl=600,
        )
    
    async def get_vector_search_with_cache(
        self,
        query: str,
        k: int,
        search_func: Callable[[str, int], Any],
        use_cache: bool = True,
        use_batching: bool = True,
    ) -> list[tuple[str, dict[str, Any], float]]:
        """带缓存的向量检索"""
        # 尝试从缓存获取
        if use_cache:
            cached = await self.vector_search_cache.get(query, k)
            if cached is not None:
                return cached
        
        # 执行检索
        if use_batching:
            results = await self.batch_optimizer.execute_with_batching(
                query, k, search_func
            )
        else:
            results = await search_func(query, k)
        
        # 去重
        results = self.deduplicator.deduplicate(results)
        
        # 存入缓存
        if use_cache:
            await self.vector_search_cache.set(query, results, k)
        
        return results
    
    async def get_ai_response_with_cache(
        self,
        question: str,
        generate_func: Callable[[], Any],
        context_hash: str = "",
        priority: CachePriority = CachePriority.MEDIUM,
        use_cache: bool = True,
    ) -> tuple[str, AIResponseCacheEntry | None]:
        """带缓存的 AI 响应生成"""
        # 尝试从缓存获取
        if use_cache:
            cached = await self.response_cache.get(question, context_hash)
            if cached is not None:
                return cached.answer, cached
        
        # 执行生成
        result = await generate_func()
        answer, references, model_used, confidence = result
        
        # 存入缓存
        cache_key = ""
        if use_cache:
            cache_key = await self.response_cache.set(
                question=question,
                answer=answer,
                references=references,
                model_used=model_used,
                confidence=confidence,
                context_hash=context_hash,
                priority=priority,
            )
        
        return answer, None
    
    async def execute_with_retry(
        self,
        request_func: Callable[[], Any],
        timeout: float | None = None,
        retry_config: RetryConfig | None = None,
    ) -> Any:
        """带重试机制的请求执行"""
        return await self.request_executor.execute(
            request_func, timeout, retry_config
        )
    
    async def submit_to_queue(
        self,
        request_func: Callable[[], Any],
        priority: int = 5,
        timeout: float | None = None,
    ) -> Any:
        """提交请求到队列"""
        return await self.queue_manager.submit(request_func, priority, timeout)
    
    async def invalidate_all_caches(
        self,
        reason: CacheInvalidationReason = CacheInvalidationReason.MANUAL_INVALIDATE,
    ) -> dict[str, int]:
        """使所有缓存失效"""
        results = {}
        
        # 失效向量检索缓存
        results["vector_search"] = await self.vector_search_cache.invalidate_all()
        
        # 失效 AI 响应缓存
        results["ai_response"] = await self.response_cache.invalidate_all(reason)
        
        logger.info(f"All AI caches invalidated: {results}")
        return results
    
    def get_all_stats(self) -> dict[str, Any]:
        """获取所有缓存和优化器的统计信息"""
        return {
            "vector_search_cache": self.vector_search_cache.get_stats(),
            "ai_response_cache": self.response_cache.get_stats(),
            "batch_optimizer": self.batch_optimizer.get_stats(),
            "queue_manager": self.queue_manager.get_stats(),
            "request_executor": self.request_executor.get_stats(),
            "multi_level_cache": self._multi_level_cache.get_stats().to_dict(),
        }


# 全局单例
_ai_cache_optimizer: AICacheOptimizer | None = None


def get_ai_cache_optimizer() -> AICacheOptimizer:
    """获取 AI 缓存优化器单例"""
    global _ai_cache_optimizer
    if _ai_cache_optimizer is None:
        _ai_cache_optimizer = AICacheOptimizer()
    return _ai_cache_optimizer