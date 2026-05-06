"""AI服务监控指标"""
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class LLMMetrics:
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_tokens: int = 0
    total_latency_ms: int = 0
    timeout_calls: int = 0
    circuit_breaker_trips: int = 0

    @property
    def success_rate(self) -> float:
        return self.successful_calls / self.total_calls if self.total_calls > 0 else 0.0

    @property
    def average_latency_ms(self) -> float:
        return self.total_latency_ms / self.total_calls if self.total_calls > 0 else 0.0


@dataclass
class RAGMetrics:
    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    level1_hits: int = 0
    level2_hits: int = 0
    level3_fallbacks: int = 0
    total_latency_ms: int = 0
    avg_similarity: float = 0.0
    similarity_sum: float = 0.0

    @property
    def cache_hit_rate(self) -> float:
        return self.cache_hits / self.total_queries if self.total_queries > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.total_queries if self.total_queries > 0 else 0.0


@dataclass
class AgentMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    intent_classifications: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    hallucination_detections: int = 0
    hallucination_blocks: int = 0
    node_latencies: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def success_rate(self) -> float:
        return self.successful_requests / self.total_requests if self.total_requests > 0 else 0.0

    @property
    def hallucination_block_rate(self) -> float:
        return self.hallucination_blocks / self.hallucination_detections if self.hallucination_detections > 0 else 0.0


@dataclass
class SessionMetrics:
    total_sessions: int = 0
    active_sessions: int = 0
    total_messages: int = 0
    avg_messages_per_session: float = 0.0
    avg_session_duration_seconds: float = 0.0


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.llm = LLMMetrics()
        self.rag = RAGMetrics()
        self.agent = AgentMetrics()
        self.session = SessionMetrics()

        self._lock = asyncio.Lock()
        self._request_start_times: Dict[str, float] = {}

    async def record_llm_call(
        self,
        success: bool,
        latency_ms: int,
        tokens_used: int = 0,
        timeout: bool = False,
        error: str = None
    ):
        """记录LLM调用"""
        async with self._lock:
            self.llm.total_calls += 1
            self.llm.total_latency_ms += latency_ms
            self.llm.total_tokens += tokens_used

            if success:
                self.llm.successful_calls += 1
            else:
                self.llm.failed_calls += 1
                if timeout:
                    self.llm.timeout_calls += 1

    async def record_circuit_breaker_trip(self):
        """记录熔断器触发"""
        async with self._lock:
            self.llm.circuit_breaker_trips += 1

    async def record_rag_query(
        self,
        cached: bool = False,
        level: str = "level_1",
        latency_ms: int = 0,
        similarity: float = 0.0
    ):
        """记录RAG查询"""
        async with self._lock:
            self.rag.total_queries += 1
            self.rag.total_latency_ms += latency_ms
            self.rag.similarity_sum += similarity

            if cached:
                self.rag.cache_hits += 1
            elif level == "level_1_local":
                self.rag.level1_hits += 1
            elif level == "level_2_backend":
                self.rag.level2_hits += 1
            elif level == "level_3_fallback":
                self.rag.level3_fallbacks += 1

    async def record_agent_request(
        self,
        success: bool,
        intent: str = None,
        hallucination_detected: bool = False,
        hallucination_blocked: bool = False
    ):
        """记录Agent请求"""
        async with self._lock:
            self.agent.total_requests += 1

            if success:
                self.agent.successful_requests += 1
            else:
                self.agent.failed_requests += 1

            if intent:
                self.agent.intent_classifications[intent] += 1

            if hallucination_detected:
                self.agent.hallucination_detections += 1
            if hallucination_blocked:
                self.agent.hallucination_blocks += 1

    async def record_node_latency(self, node_name: str, latency_ms: int):
        """记录节点延迟"""
        async with self._lock:
            self.agent.node_latencies[node_name] += latency_ms

    async def record_session(self, message_count: int = 0):
        """记录会话"""
        async with self._lock:
            self.session.total_sessions += 1
            self.session.total_messages += message_count

    async def get_metrics(self) -> dict:
        """获取所有指标"""
        async with self._lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "llm": {
                    "total_calls": self.llm.total_calls,
                    "successful_calls": self.llm.successful_calls,
                    "failed_calls": self.llm.failed_calls,
                    "success_rate": round(self.llm.success_rate * 100, 2),
                    "average_latency_ms": round(self.llm.average_latency_ms, 2),
                    "total_tokens": self.llm.total_tokens,
                    "timeout_calls": self.llm.timeout_calls,
                    "circuit_breaker_trips": self.llm.circuit_breaker_trips,
                },
                "rag": {
                    "total_queries": self.rag.total_queries,
                    "cache_hits": self.rag.cache_hits,
                    "cache_misses": self.rag.cache_misses,
                    "cache_hit_rate": round(self.rag.cache_hit_rate * 100, 2),
                    "level1_hits": self.rag.level1_hits,
                    "level2_hits": self.rag.level2_hits,
                    "level3_fallbacks": self.rag.level3_fallbacks,
                    "average_latency_ms": round(self.rag.avg_latency_ms, 2),
                    "average_similarity": round(
                        self.rag.similarity_sum / self.rag.total_queries
                        if self.rag.total_queries > 0 else 0.0, 3
                    ),
                },
                "agent": {
                    "total_requests": self.agent.total_requests,
                    "successful_requests": self.agent.successful_requests,
                    "failed_requests": self.agent.failed_requests,
                    "success_rate": round(self.agent.success_rate * 100, 2),
                    "intent_classifications": dict(self.agent.intent_classifications),
                    "hallucination_detections": self.agent.hallucination_detections,
                    "hallucination_blocks": self.agent.hallucination_blocks,
                    "hallucination_block_rate": round(self.agent.hallucination_block_rate * 100, 2),
                    "node_latencies": dict(self.agent.node_latencies),
                },
                "session": {
                    "total_sessions": self.session.total_sessions,
                    "active_sessions": self.session.active_sessions,
                    "total_messages": self.session.total_messages,
                    "average_messages_per_session": round(
                        self.session.total_messages / self.session.total_sessions
                        if self.session.total_sessions > 0 else 0.0, 2
                    ),
                }
            }

    async def reset(self):
        """重置指标"""
        async with self._lock:
            self.llm = LLMMetrics()
            self.rag = RAGMetrics()
            self.agent = AgentMetrics()
            self.session = SessionMetrics()
            self._request_start_times.clear()


_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


class MetricsContext:
    """指标上下文管理器"""

    def __init__(self, metric_type: str, operation: str):
        self.metric_type = metric_type
        self.operation = operation
        self.start_time = None

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        latency_ms = int((time.time() - self.start_time) * 1000)
        collector = get_metrics_collector()

        if self.metric_type == "llm":
            await collector.record_llm_call(
                success=exc_type is None,
                latency_ms=latency_ms
            )
        elif self.metric_type == "rag":
            await collector.record_rag_query(
                latency_ms=latency_ms
            )
        elif self.metric_type == "agent":
            await collector.record_agent_request(
                success=exc_type is None
            )

        return False
