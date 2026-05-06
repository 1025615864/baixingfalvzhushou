"""社区服务监控指标"""
import time
import logging
from typing import Optional, Dict
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class PostMetrics:
    total_posts: int = 0
    published_posts: int = 0
    deleted_posts: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_favorites: int = 0
    search_queries: int = 0


@dataclass
class APIMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: int = 0
    by_endpoint: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_status: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


@dataclass
class CacheMetrics:
    hits: int = 0
    misses: int = 0
    sets: int = 0
    invalidations: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


@dataclass
class KafkaMetrics:
    events_published: int = 0
    events_consumed: int = 0
    publish_errors: int = 0
    consume_errors: int = 0


class CommunityMetricsCollector:
    def __init__(self):
        self.post = PostMetrics()
        self.api = APIMetrics()
        self.cache = CacheMetrics()
        self.kafka = KafkaMetrics()
        self._lock = asyncio.Lock()

    async def record_post_created(self):
        async with self._lock:
            self.post.total_posts += 1
            self.post.published_posts += 1

    async def record_post_viewed(self, views: int = 1):
        async with self._lock:
            self.post.total_views += views

    async def record_post_liked(self, liked: bool):
        async with self._lock:
            if liked:
                self.post.total_likes += 1
            else:
                self.post.total_likes = max(0, self.post.total_likes - 1)

    async def record_comment_added(self):
        async with self._lock:
            self.post.total_comments += 1

    async def record_favorite_added(self, added: bool):
        async with self._lock:
            if added:
                self.post.total_favorites += 1
            else:
                self.post.total_favorites = max(0, self.post.total_favorites - 1)

    async def record_search_query(self):
        async with self._lock:
            self.post.search_queries += 1

    async def record_api_request(
        self,
        endpoint: str,
        status_code: int,
        latency_ms: int,
        success: bool
    ):
        async with self._lock:
            self.api.total_requests += 1
            self.api.by_endpoint[endpoint] += 1
            self.api.by_status[str(status_code)] += 1
            self.api.total_latency_ms += latency_ms

            if success:
                self.api.successful_requests += 1
            else:
                self.api.failed_requests += 1

    async def record_cache_hit(self):
        async with self._lock:
            self.cache.hits += 1

    async def record_cache_miss(self):
        async with self._lock:
            self.cache.misses += 1

    async def record_cache_set(self):
        async with self._lock:
            self.cache.sets += 1

    async def record_cache_invalidation(self):
        async with self._lock:
            self.cache.invalidations += 1

    async def record_kafka_published(self):
        async with self._lock:
            self.kafka.events_published += 1

    async def record_kafka_consumed(self):
        async with self._lock:
            self.kafka.events_consumed += 1

    async def record_kafka_error(self, publish: bool = True):
        async with self._lock:
            if publish:
                self.kafka.publish_errors += 1
            else:
                self.kafka.consume_errors += 1

    async def get_metrics(self) -> dict:
        async with self._lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "post": {
                    "total_posts": self.post.total_posts,
                    "published_posts": self.post.published_posts,
                    "deleted_posts": self.post.deleted_posts,
                    "total_views": self.post.total_views,
                    "total_likes": self.post.total_likes,
                    "total_comments": self.post.total_comments,
                    "total_favorites": self.post.total_favorites,
                    "search_queries": self.post.search_queries,
                },
                "api": {
                    "total_requests": self.api.total_requests,
                    "successful_requests": self.api.successful_requests,
                    "failed_requests": self.api.failed_requests,
                    "success_rate": round(
                        self.api.successful_requests / self.api.total_requests * 100
                        if self.api.total_requests > 0 else 0.0, 2
                    ),
                    "average_latency_ms": round(
                        self.api.total_latency_ms / self.api.total_requests
                        if self.api.total_requests > 0 else 0.0, 2
                    ),
                    "by_endpoint": dict(self.api.by_endpoint),
                    "by_status": dict(self.api.by_status),
                },
                "cache": {
                    "hits": self.cache.hits,
                    "misses": self.cache.misses,
                    "sets": self.cache.sets,
                    "invalidations": self.cache.invalidations,
                    "hit_rate": round(self.cache.hit_rate * 100, 2),
                },
                "kafka": {
                    "events_published": self.kafka.events_published,
                    "events_consumed": self.kafka.events_consumed,
                    "publish_errors": self.kafka.publish_errors,
                    "consume_errors": self.kafka.consume_errors,
                }
            }

    async def reset(self):
        async with self._lock:
            self.post = PostMetrics()
            self.api = APIMetrics()
            self.cache = CacheMetrics()
            self.kafka = KafkaMetrics()


_metrics_collector: Optional[CommunityMetricsCollector] = None


def get_metrics_collector() -> CommunityMetricsCollector:
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = CommunityMetricsCollector()
    return _metrics_collector


class MetricsContext:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.start_time = None

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        latency_ms = int((time.time() - self.start_time) * 1000)
        status_code = 200 if exc_type is None else 500
        collector = get_metrics_collector()
        await collector.record_api_request(
            endpoint=self.endpoint,
            status_code=status_code,
            latency_ms=latency_ms,
            success=exc_type is None
        )
        return False
