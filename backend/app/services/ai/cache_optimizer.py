"""AI cache optimizer service."""
from __future__ import annotations
import asyncio
import enum
import time
from typing import Optional, Any
from dataclasses import dataclass, field


class CachePriority(enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CacheInvalidationReason(enum.Enum):
    TTL_EXPIRED = "ttl_expired"
    MANUAL_INVALIDATE = "manual_invalidate"
    KNOWLEDGE_BASE_UPDATE = "knowledge_base_update"
    USER_FEEDBACK = "user_feedback"


class RetryStrategy(enum.Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


@dataclass
class RetryConfig:
    strategy: RetryStrategy = RetryStrategy.FIXED
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0

    def get_delay(self, attempt: int) -> float:
        if self.strategy == RetryStrategy.FIXED:
            return self.base_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** attempt)
            return min(delay, self.max_delay)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
            return min(delay, self.max_delay)
        return self.base_delay


@dataclass
class VectorSearchCacheEntry:
    query: str
    k: int
    results: list
    timestamp: float


class VectorSearchCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self._cache: dict[str, VectorSearchCacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def _key(self, query: str, k: int) -> str:
        return f"{query}::{k}"

    def get_sync(self, query: str, k: int = 5) -> Optional[list]:
        key = self._key(query, k)
        entry = self._cache.get(key)
        if entry and (time.time() - entry.timestamp) < self._default_ttl:
            self._hits += 1
            return entry.results
        self._misses += 1
        return None

    def set_sync(self, query: str, results: list, k: int = 5) -> None:
        key = self._key(query, k)
        self._cache[key] = VectorSearchCacheEntry(query=query, k=k, results=results, timestamp=time.time())
        if len(self._cache) > self._max_size:
            oldest = min(self._cache.items(), key=lambda x: x[1].timestamp)
            del self._cache[oldest[0]]

    async def get(self, query: str, k: int = 5) -> Optional[list]:
        return self.get_sync(query, k)

    async def set(self, query: str, results: list, k: int = 5) -> None:
        self.set_sync(query, results, k)

    def get_stats(self) -> dict:
        return {"hits": self._hits, "misses": self._misses, "size": len(self._cache)}


@dataclass
class AIResponseCacheEntry:
    question: str
    answer: str
    references: list
    model_used: str
    confidence: str
    priority: CachePriority = CachePriority.MEDIUM
    timestamp: float = 0.0
    feedback: list = field(default_factory=list)


class AIResponseCache:
    def __init__(self, high_priority_ttl: int = 7200, default_ttl: int = 3600, low_priority_ttl: int = 1800):
        self._cache: dict[str, AIResponseCacheEntry] = {}
        self._high_priority_ttl = high_priority_ttl
        self._default_ttl = default_ttl
        self._low_priority_ttl = low_priority_ttl
        self._feedback_threshold = 3

    def _get_ttl(self, priority: CachePriority) -> int:
        if priority == CachePriority.HIGH:
            return self._high_priority_ttl
        elif priority == CachePriority.LOW:
            return self._low_priority_ttl
        return self._default_ttl

    async def get(self, question: str) -> Optional[AIResponseCacheEntry]:
        entry = self._cache.get(question)
        if entry is None:
            return None
        ttl = self._get_ttl(entry.priority)
        if time.time() - entry.timestamp > ttl:
            del self._cache[question]
            return None
        if len(entry.feedback) >= self._feedback_threshold:
            del self._cache[question]
            return None
        return entry

    async def set(self, question: str, answer: str, references: list, model_used: str, confidence: str, priority: CachePriority = CachePriority.MEDIUM) -> str:
        key = question
        self._cache[key] = AIResponseCacheEntry(
            question=question, answer=answer, references=references,
            model_used=model_used, confidence=confidence, priority=priority,
            timestamp=time.time(),
        )
        return key

    async def add_feedback(self, cache_key: str, feedback_type: str) -> None:
        entry = self._cache.get(cache_key)
        if entry:
            entry.feedback.append(feedback_type)

    def get_stats(self) -> dict:
        dist = {"high": 0, "medium": 0, "low": 0}
        for e in self._cache.values():
            dist[e.priority.value] = dist.get(e.priority.value, 0) + 1
        return {"priority_distribution": dist, "size": len(self._cache)}


class ResultDeduplicator:
    def deduplicate(self, results: list[tuple[str, dict, float]]) -> list[tuple[str, dict, float]]:
        seen_ids = set()
        seen_hashes = set()
        deduped = []
        for content, metadata, score in results:
            kid = metadata.get("knowledge_id")
            content_hash = hash(content)
            if kid and kid in seen_ids:
                continue
            if not kid and content_hash in seen_hashes:
                continue
            if kid:
                seen_ids.add(kid)
            seen_hashes.add(content_hash)
            deduped.append((content, metadata, score))
        return deduped

    def merge_and_deduplicate(self, result_sets: list[list[tuple]], max_results: int = 10) -> list[tuple]:
        merged = []
        for rs in result_sets:
            merged.extend(rs)
        deduped = self.deduplicate(merged)
        deduped.sort(key=lambda x: x[2], reverse=True)
        return deduped[:max_results]


class BatchRetrievalOptimizer:
    def __init__(self, batch_window_ms: int = 50):
        self._batch_window_ms = batch_window_ms
        self._pending: dict[str, list] = {}

    async def execute_with_batching(self, query: str, k: int, search_func) -> list:
        key = f"{query}::{k}"
        future = asyncio.get_event_loop().create_future()
        if key not in self._pending:
            self._pending[key] = []
            self._pending[key].append(future)
            try:
                result = await search_func(query, k)
                for f in self._pending.pop(key, []):
                    if not f.done():
                        f.set_result(result)
            except Exception as e:
                for f in self._pending.pop(key, []):
                    if not f.done():
                        f.set_exception(e)
        else:
            self._pending[key].append(future)
        return await future


class RequestQueueManager:
    def __init__(self, max_concurrent: int = 10, queue_size: int = 100):
        self._max_concurrent = max_concurrent
        self._queue_size = queue_size
        self._completed = 0

    async def submit(self, request_func, priority: int = 5) -> Any:
        result = await request_func()
        self._completed += 1
        return result

    def get_stats(self) -> dict:
        return {"requests_completed": self._completed}


class AIRequestExecutor:
    def __init__(self, default_timeout: float = 30.0):
        self._default_timeout = default_timeout
        self._stats = {"successful_requests": 0, "timeout_requests": 0, "retried_requests": 0}

    async def execute(self, func, retry_config: Optional[RetryConfig] = None, timeout: Optional[float] = None) -> Any:
        to = timeout or self._default_timeout
        attempts = 0
        max_attempts = 1
        if retry_config:
            max_attempts = retry_config.max_retries + 1
        while attempts < max_attempts:
            try:
                result = await asyncio.wait_for(func(), timeout=to)
                self._stats["successful_requests"] += 1
                return result
            except asyncio.TimeoutError:
                self._stats["timeout_requests"] += 1
                raise TimeoutError()
            except Exception:
                attempts += 1
                if retry_config and attempts < max_attempts:
                    self._stats["retried_requests"] += 1
                    delay = retry_config.get_delay(attempts - 1)
                    await asyncio.sleep(delay)
                else:
                    raise

    def get_stats(self) -> dict:
        return self._stats


class AICacheOptimizer:
    def __init__(self):
        self._vector_cache = VectorSearchCache()
        self._response_cache = AIResponseCache()
        self._batch_optimizer = BatchRetrievalOptimizer()
        self._queue_manager = RequestQueueManager()
        self._request_executor = AIRequestExecutor()

    def get_all_stats(self) -> dict:
        return {
            "vector_search_cache": self._vector_cache.get_stats(),
            "ai_response_cache": self._response_cache.get_stats(),
            "batch_optimizer": {},
            "queue_manager": self._queue_manager.get_stats(),
            "request_executor": self._request_executor.get_stats(),
        }


_instance: Optional[AICacheOptimizer] = None


def get_ai_cache_optimizer() -> AICacheOptimizer:
    global _instance
    if _instance is None:
        _instance = AICacheOptimizer()
    return _instance
