"""
AI 质量监控中间件

提供 AI 咨询质量监控能力：
1. 请求/响应日志记录
2. 质量评分收集
3. 异常检测与告警
4. 统计分析接口

使用方式：
1. 在 main.py 中注册中间件
2. 调用 AILoggerService 记录交互
3. 通过 /api/system/ai-quality/stats 查看统计
"""

from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone as dt_timezone
from enum import Enum
from typing import Optional, Dict, Any, List
import logging

# 使用timezone-aware datetime
UTC = dt_timezone.utc


logger = logging.getLogger(__name__)


class AILogLevel(str, Enum):
    """AI日志级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class QualityScore(str, Enum):
    """质量评分等级"""
    EXCELLENT = "excellent"  # 4-5星
    GOOD = "good"            # 3-4星
    FAIR = "fair"            # 2-3星
    POOR = "poor"            # 1-2星


@dataclass
class AIConversationLog:
    """AI咨询日志记录"""
    request_id: str
    message_length: int
    response_length: int
    response_time_ms: int
    session_id: Optional[str] = None
    user_id: Optional[int] = None
    quality_score: Optional[int] = None  # 1-5星
    quality_feedback: Optional[str] = None
    was_helpful: Optional[bool] = None
    topics: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    token_usage: Optional[int] = None
    error_type: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat())
    level: str = AILogLevel.INFO.value

    def __post_init__(self):
        """初始化后自动设置日志级别"""
        # 根据error_type自动设置level
        if self.error_type:
            self.level = AILogLevel.ERROR.value
        # 根据quality_score自动设置level（仅当level还是默认值时）
        elif self.quality_score is not None and self.quality_score < 3 and self.level == AILogLevel.INFO.value:
            self.level = AILogLevel.WARNING.value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（JSON序列化）"""
        data = asdict(self)
        # 处理枚举类型
        if self.quality_score is not None:
            data['quality_level'] = self._get_quality_level()
        return data

    def _get_quality_level(self) -> str:
        """根据评分获取质量等级"""
        if self.quality_score is None:
            return QualityScore.FAIR.value
        if self.quality_score >= 4:
            return QualityScore.EXCELLENT.value
        elif self.quality_score >= 3:
            return QualityScore.GOOD.value
        elif self.quality_score >= 2:
            return QualityScore.FAIR.value
        else:
            return QualityScore.POOR.value


class AIQualityMetrics:
    """AI质量指标计数器（内存版，生产建议用Redis）"""

    def __init__(self):
        self._lock = __import__("threading").Lock()
        self._counters: Dict[str, int] = {}
        self._response_times: List[int] = []
        self._quality_scores: List[int] = []
        self._errors: Dict[str, int] = {}
        self._recent_logs: List[AIConversationLog] = []
        self._max_recent_logs = 1000  # 保留最近1000条

    def increment_counter(self, key: str, value: int = 1) -> None:
        """原子性增加计数器"""
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + value

    def record_response_time(self, ms: int) -> None:
        """记录响应时间"""
        with self._lock:
            self._response_times.append(ms)
            # 保留最近10000条
            if len(self._response_times) > 10000:
                self._response_times = self._response_times[-10000:]

    def record_quality_score(self, score: int) -> None:
        """记录质量评分"""
        with self._lock:
            if 1 <= score <= 5:
                self._quality_scores.append(score)
                if len(self._quality_scores) > 10000:
                    self._quality_scores = self._quality_scores[-10000:]

    def record_error(self, error_type: str) -> None:
        """记录错误类型"""
        with self._lock:
            self._errors[error_type] = self._errors.get(error_type, 0) + 1
            self._counters["total_errors"] = self._counters.get(
                "total_errors", 0) + 1

    def add_log(self, log: AIConversationLog) -> None:
        """添加日志"""
        with self._lock:
            self._recent_logs.append(log)
            if len(self._recent_logs) > self._max_recent_logs:
                self._recent_logs = self._recent_logs[-self._max_recent_logs:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "counters": self._counters.copy(),
                "response_time": self._get_response_time_stats(),
                "quality_score": self._get_quality_stats(),
                "errors": self._errors.copy(),
                "total_conversations": self._counters.get(
                    "total_requests",
                    0),
                "successful_conversations": self._counters.get(
                    "successful_responses",
                    0),
            }

    def _get_response_time_stats(self) -> Dict[str, Any]:
        """计算响应时间统计"""
        if not self._response_times:
            return {"avg_ms": 0, "p50_ms": 0,
                    "p95_ms": 0, "p99_ms": 0, "count": 0}
        sorted_times = sorted(self._response_times)
        n = len(sorted_times)
        return {
            "avg_ms": round(sum(sorted_times) / n, 2),
            "p50_ms": sorted_times[n // 2],
            "p95_ms": sorted_times[int(n * 0.95)],
            "p99_ms": sorted_times[int(n * 0.99)],
            "count": n,
        }

    def _get_quality_stats(self) -> Dict[str, Any]:
        """计算质量评分统计"""
        if not self._quality_scores:
            return {"avg": 0, "distribution": {},
                    "count": 0, "satisfaction_rate": 0}
        n = len(self._quality_scores)
        total = sum(self._quality_scores)
        distribution = {
            "excellent_45": sum(1 for s in self._quality_scores if s >= 4),
            "good_34": sum(1 for s in self._quality_scores if 3 <= s < 4),
            "fair_23": sum(1 for s in self._quality_scores if 2 <= s < 3),
            "poor_1": sum(1 for s in self._quality_scores if s < 2),
        }
        return {
            "avg": round(
                total /
                n,
                2),
            "distribution": distribution,
            "count": n,
            "satisfaction_rate": round(
                distribution["excellent_45"] /
                n *
                100,
                2) if n > 0 else 0,
        }

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的日志"""
        with self._lock:
            logs = self._recent_logs[-limit:]
            return [log.to_dict() for log in logs]

    def reset(self) -> None:
        """重置所有数据"""
        with self._lock:
            self._counters.clear()
            self._response_times.clear()
            self._quality_scores.clear()
            self._errors.clear()
            self._recent_logs.clear()


# 全局指标实例
_ai_metrics = AIQualityMetrics()


def get_ai_metrics() -> AIQualityMetrics:
    """获取AI质量指标实例"""
    return _ai_metrics


class AIQualityMiddleware(BaseHTTPMiddleware):
    """
    AI质量监控中间件

    自动记录AI相关接口的请求和响应信息
    """

    # 需要监控的路由前缀
    AI_ROUTES = {"/api/ai/chat", "/api/ai/consultations"}

    def _is_ai_route(self, path: str) -> bool:
        """判断是否是AI相关路由"""
        return any(path.startswith(route) for route in self.AI_ROUTES)

    async def dispatch(self, request: Request, call_next):
        # 检查是否是AI相关路由
        path = request.url.path
        if not any(path.startswith(route) for route in self.AI_ROUTES):
            return await call_next(request)

        # 获取request_id
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        start_time = time.time()

        # 记录请求
        _ai_metrics.increment_counter("total_requests")

        try:
            response = await call_next(request)
            response_time = int((time.time() - start_time) * 1000)

            # 记录成功响应
            _ai_metrics.increment_counter("successful_responses")
            _ai_metrics.record_response_time(response_time)

            # 在响应头添加request_id
            response.headers["X-Request-Id"] = request_id

            return response

        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            error_type = type(e).__name__

            # 记录错误
            _ai_metrics.increment_counter("total_errors")
            _ai_metrics.record_error(error_type)

            logger.error(
                f"AI request failed: request_id={request_id}, "
                f"error={error_type}, time_ms={response_time}"
            )

            # 返回错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "AI service error",
                    "request_id": request_id,
                    "error_type": error_type,
                }
            )


class AILoggerService:
    """
    AI对话日志服务

    用于记录AI咨询的详细交互信息
    """

    def __init__(self, metrics: Optional[AIQualityMetrics] = None):
        self._metrics = metrics or _ai_metrics

    def log_conversation(
        self,
        request_id: str,
        session_id: Optional[str],
        user_id: Optional[int],
        message_length: int,
        response_length: int,
        response_time_ms: int,
        quality_score: Optional[int] = None,
        quality_feedback: Optional[str] = None,
        was_helpful: Optional[bool] = None,
        topics: Optional[List[str]] = None,
        tools_used: Optional[List[str]] = None,
        token_usage: Optional[int] = None,
        error_type: Optional[str] = None,
    ) -> AIConversationLog:
        """
        记录一次AI对话

        Args:
            request_id: 请求ID
            session_id: 会话ID
            user_id: 用户ID
            message_length: 消息长度
            response_length: 响应长度
            response_time_ms: 响应时间（毫秒）
            quality_score: 质量评分（1-5星）
            quality_feedback: 质量反馈文字
            was_helpful: 是否有用
            topics: 涉及的法律领域
            tools_used: 使用的工具列表
            token_usage: Token使用量
            error_type: 错误类型

        Returns:
            AIConversationLog: 日志记录
        """
        # 确定日志级别
        level = AILogLevel.INFO.value
        if error_type:
            level = AILogLevel.ERROR.value
        elif quality_score is not None and quality_score < 3:
            level = AILogLevel.WARNING.value

        log = AIConversationLog(
            request_id=request_id,
            session_id=session_id,
            user_id=user_id,
            message_length=message_length,
            response_length=response_length,
            response_time_ms=response_time_ms,
            quality_score=quality_score,
            quality_feedback=quality_feedback,
            was_helpful=was_helpful,
            topics=topics or [],
            tools_used=tools_used or [],
            token_usage=token_usage,
            error_type=error_type,
            level=level,
        )

        # 记录到指标系统
        self._metrics.add_log(log)

        # 更新计数器
        self._metrics.increment_counter("total_requests")
        self._metrics.record_response_time(response_time_ms)

        if quality_score is not None:
            self._metrics.record_quality_score(quality_score)

        if error_type:
            self._metrics.record_error(error_type)
        else:
            self._metrics.increment_counter("successful_responses")

        # 记录涉及的法律领域
        if topics:
            for topic in topics:
                self._metrics.increment_counter(f"topic_{topic}")

        # 记录使用的工具
        if tools_used:
            for tool in tools_used:
                self._metrics.increment_counter(f"tool_{tool}")

        logger.info(
            f"AI conversation logged: request_id={request_id}, "
            f"session={session_id}, score={quality_score}, "
            f"time_ms={response_time_ms}"
        )

        return log

    def log_feedback(
        self,
        request_id: str,
        is_positive: bool,
        feedback_text: Optional[str] = None,
    ) -> None:
        """
        记录用户反馈

        Args:
            request_id: 请求ID
            is_positive: 是否正面反馈
            feedback_text: 反馈文字
        """
        self._metrics.increment_counter(
            "positive_feedback" if is_positive else "negative_feedback")

        if is_positive:
            self._metrics.increment_counter("helpful_responses")
        else:
            self._metrics.increment_counter("unhelpful_responses")

        logger.info(
            f"AI feedback recorded: request_id={request_id}, "
            f"positive={is_positive}"
        )

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._metrics.get_stats()

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的日志"""
        return self._metrics.get_recent_logs(limit)


def get_ai_logger() -> AILoggerService:
    """获取AI日志服务实例"""
    return AILoggerService()


# ===================== Redis持久化支持（生产环境） =====================

class RedisAIQualityMetrics:
    """
    Redis版本的AI质量指标存储（生产环境推荐）

    特性：
    - 指标持久化到Redis，应用重启后数据不丢失
    - 支持多实例共享指标
    - 自动过期清理
    """

    def __init__(
        self,
        redis_client,
        key_prefix: str = "ai_quality:",
        max_recent_logs: int = 1000,
        ttl_seconds: int = 86400 * 7,  # 7天过期
    ):
        self._redis = redis_client
        self._key_prefix = key_prefix
        self._max_recent_logs = max_recent_logs
        self._ttl_seconds = ttl_seconds

        # 缓存计数器，避免频繁Redis调用
        self._counters_cache: Dict[str, int] = {}
        self._response_times_cache: List[int] = []
        self._quality_scores_cache: List[int] = []
        self._cache_dirty = False

    def _key(self, suffix: str) -> str:
        """生成Redis key"""
        return f"{self._key_prefix}{suffix}"

    async def initialize(self) -> None:
        """从Redis加载缓存数据"""
        try:
            # 加载计数器
            counters_data = await self._redis.get(self._key("counters"))
            if counters_data:
                import json
                self._counters_cache = json.loads(counters_data)

            # 加载响应时间
            response_times_data = await self._redis.get(self._key("response_times"))
            if response_times_data:
                import json
                self._response_times_cache = json.loads(response_times_data)

            # 加载质量评分
            quality_scores_data = await self._redis.get(self._key("quality_scores"))
            if quality_scores_data:
                import json
                self._quality_scores_cache = json.loads(quality_scores_data)

            logger.info(
                f"AI质量指标从Redis加载完成: {len(self._counters_cache)} counters")
        except Exception as e:
            logger.warning(f"从Redis加载AI质量指标失败，使用空指标: {e}")

    async def _persist_counters(self) -> None:
        """持久化计数器到Redis"""
        import json
        await self._redis.setex(
            self._key("counters"),
            self._ttl_seconds,
            json.dumps(self._counters_cache, default=str),
        )

    async def _persist_response_times(self) -> None:
        """持久化响应时间到Redis"""
        import json
        # 只保留最近10000条
        times = self._response_times_cache[-10000:]
        await self._redis.setex(
            self._key("response_times"),
            self._ttl_seconds,
            json.dumps(times, default=str),
        )

    async def _persist_quality_scores(self) -> None:
        """持久化质量评分到Redis"""
        import json
        # 只保留最近10000条
        scores = self._quality_scores_cache[-10000:]
        await self._redis.setex(
            self._key("quality_scores"),
            self._ttl_seconds,
            json.dumps(scores, default=str),
        )

    def increment_counter(self, key: str, value: int = 1) -> None:
        """原子性增加计数器"""
        self._counters_cache[key] = self._counters_cache.get(key, 0) + value
        self._cache_dirty = True

    def record_response_time(self, ms: int) -> None:
        """记录响应时间"""
        self._response_times_cache.append(ms)
        if len(self._response_times_cache) > 10000:
            self._response_times_cache = self._response_times_cache[-10000:]
        self._cache_dirty = True

    def record_quality_score(self, score: int) -> None:
        """记录质量评分"""
        if 1 <= score <= 5:
            self._quality_scores_cache.append(score)
            if len(self._quality_scores_cache) > 10000:
                self._quality_scores_cache = self._quality_scores_cache[-10000:]
            self._cache_dirty = True

    def record_error(self, error_type: str) -> None:
        """记录错误类型"""
        self._counters_cache[f"error_{error_type}"] = (
            self._counters_cache.get(f"error_{error_type}", 0) + 1
        )
        self._counters_cache["total_errors"] = (
            self._counters_cache.get("total_errors", 0) + 1
        )
        self._cache_dirty = True

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "counters": self._counters_cache.copy(),
            "response_time": self._get_response_time_stats(),
            "quality_score": self._get_quality_stats(),
            "total_conversations": self._counters_cache.get(
                "total_requests",
                0),
            "successful_conversations": self._counters_cache.get(
                "successful_responses",
                0),
        }

    def _get_response_time_stats(self) -> Dict[str, Any]:
        """计算响应时间统计"""
        if not self._response_times_cache:
            return {"avg_ms": 0, "p50_ms": 0,
                    "p95_ms": 0, "p99_ms": 0, "count": 0}
        sorted_times = sorted(self._response_times_cache)
        n = len(sorted_times)
        return {
            "avg_ms": round(sum(sorted_times) / n, 2),
            "p50_ms": sorted_times[n // 2],
            "p95_ms": sorted_times[int(n * 0.95)],
            "p99_ms": sorted_times[int(n * 0.99)],
            "count": n,
        }

    def _get_quality_stats(self) -> Dict[str, Any]:
        """计算质量评分统计"""
        if not self._quality_scores_cache:
            return {"avg": 0, "distribution": {},
                    "count": 0, "satisfaction_rate": 0}
        n = len(self._quality_scores_cache)
        total = sum(self._quality_scores_cache)
        distribution = {
            "excellent_45": sum(1 for s in self._quality_scores_cache if s >= 4),
            "good_34": sum(1 for s in self._quality_scores_cache if 3 <= s < 4),
            "fair_23": sum(1 for s in self._quality_scores_cache if 2 <= s < 3),
            "poor_1": sum(1 for s in self._quality_scores_cache if s < 2),
        }
        return {
            "avg": round(
                total /
                n,
                2),
            "distribution": distribution,
            "count": n,
            "satisfaction_rate": round(
                distribution["excellent_45"] /
                n *
                100,
                2) if n > 0 else 0,
        }

    async def persist_all(self) -> None:
        """持久化所有数据到Redis"""
        if not self._cache_dirty:
            return

        try:
            await self._persist_counters()
            await self._persist_response_times()
            await self._persist_quality_scores()
            self._cache_dirty = False
            logger.debug("AI质量指标已持久化到Redis")
        except Exception as e:
            logger.warning(f"持久化AI质量指标到Redis失败: {e}")

    def reset(self) -> None:
        """重置所有数据"""
        self._counters_cache.clear()
        self._response_times_cache.clear()
        self._quality_scores_cache.clear()
        self._cache_dirty = True


# 全局Redis指标实例
_redis_ai_metrics: Optional[RedisAIQualityMetrics] = None


async def get_redis_ai_metrics(redis_client) -> RedisAIQualityMetrics:
    """获取或创建Redis AI质量指标实例"""
    global _redis_ai_metrics
    if _redis_ai_metrics is None:
        _redis_ai_metrics = RedisAIQualityMetrics(redis_client)
        await _redis_ai_metrics.initialize()
    return _redis_ai_metrics


# ===================== Prometheus指标导出 =====================

class AIQualityPrometheusExporter:
    """
    AI质量指标Prometheus导出器

    将AI质量指标转换为Prometheus格式，支持Grafana集成
    """

    def __init__(self, metrics: Optional[AIQualityMetrics] = None):
        self._metrics = metrics or _ai_metrics

    def render_metrics(self) -> str:
        """
        渲染Prometheus格式的指标

        Returns:
            str: Prometheus格式的指标文本
        """
        stats = self._metrics.get_stats()

        lines: list[str] = []

        # 帮助文本
        lines.append(
            "# HELP baixing_ai_quality_conversations_total Total AI conversations")
        lines.append("# TYPE baixing_ai_quality_conversations_total counter")
        lines.append(
            f"baixing_ai_quality_conversations_total {stats['total_conversations']}"
        )

        lines.append(
            "# HELP baixing_ai_quality_successful_conversations Total successful AI conversations")
        lines.append(
            "# TYPE baixing_ai_quality_successful_conversations counter")
        lines.append(
            f"baixing_ai_quality_successful_conversations {stats['successful_conversations']}"
        )

        lines.append("# HELPbaixing_ai_quality_errors_total Total AI errors")
        lines.append("# TYPE baixing_ai_quality_errors_total counter")
        lines.append(
            f"baixing_ai_quality_errors_total {stats['counters'].get('total_errors', 0)}"
        )

        # 响应时间指标
        response_time = stats.get("response_time", {})
        lines.append(
            "# HELP baixing_ai_quality_response_time_seconds AI response time in seconds")
        lines.append(
            "# TYPE baixing_ai_quality_response_time_seconds histogram")
        if response_time.get("count", 0) > 0:
            avg_seconds = response_time["avg_ms"] / 1000.0
            lines.append(
                f"baixing_ai_quality_response_time_seconds_bucket{{le=\"0.1\"}} {response_time['count']}")
            lines.append(
                f"baixing_ai_quality_response_time_seconds_bucket{{le=\"0.5\"}} {response_time['count']}")
            lines.append(
                f"baixing_ai_quality_response_time_seconds_bucket{{le=\"1.0\"}} {response_time['count']}")
            lines.append(
                f"baixing_ai_quality_response_time_seconds_bucket{{le=\"2.0\"}} {response_time['count']}")
            lines.append(
                f"baixing_ai_quality_response_time_seconds_bucket{{le=\"+Inf\"}} {response_time['count']}")
            lines.append(
                f"baixing_ai_quality_response_time_seconds_sum {avg_seconds * response_time['count']}")
            lines.append(
                f"baixing_ai_quality_response_time_seconds_count {response_time['count']}")

        # 质量评分指标
        quality = stats.get("quality_score", {})
        lines.append(
            "# HELP baixing_ai_quality_score_avg Average AI quality score (1-5)")
        lines.append("# TYPE baixing_ai_quality_score_avg gauge")
        lines.append(f"baixing_ai_quality_score_avg {quality.get('avg', 0)}")

        lines.append(
            "# HELP baixing_ai_quality_score_satisfaction_rate Satisfaction rate (4-5 stars percentage)")
        lines.append("# TYPE baixing_ai_quality_score_satisfaction_rate gauge")
        lines.append(
            f"baixing_ai_quality_score_satisfaction_rate {quality.get('satisfaction_rate', 0)}"
        )

        # 分布指标
        distribution = quality.get("distribution", {})
        lines.append(
            "# HELP baixing_ai_quality_score_distribution AI quality score distribution")
        lines.append("# TYPE baixing_ai_quality_score_distribution counter")
        for level, count in distribution.items():
            lines.append(
                f"baixing_ai_quality_score_distribution{{level=\"{level}\"}} {count}")

        # 错误类型分布
        lines.append(
            "# HELP baixing_ai_quality_error_type_total Total errors by type")
        lines.append("# TYPE baixing_ai_quality_error_type_total counter")
        for key, value in stats["counters"].items():
            if key.startswith("error_"):
                error_type = key[6:]  # 去掉 "error_" 前缀
                lines.append(
                    f'baixing_ai_quality_error_type_total{{type="{error_type}"}} {value}')

        # 话题分布
        lines.append(
            "# HELP baixing_ai_quality_topic_total Conversations by topic")
        lines.append("# TYPE baixing_ai_quality_topic_total counter")
        for key, value in stats["counters"].items():
            if key.startswith("topic_"):
                topic = key[6:]  # 去掉 "topic_" 前缀
                lines.append(
                    f'baixing_ai_quality_topic_total{{topic="{topic}"}} {value}')

        # 工具使用分布
        lines.append("# HELP baixing_ai_quality_tool_total Tool usage by type")
        lines.append("# TYPE baixing_ai_quality_tool_total counter")
        for key, value in stats["counters"].items():
            if key.startswith("tool_"):
                tool = key[5:]  # 去掉 "tool_" 前缀
                lines.append(
                    f'baixing_ai_quality_tool_total{{tool="{tool}"}} {value}')

        return "\n".join(lines)


# 全局导出器实例
_ai_quality_prometheus_exporter: Optional[AIQualityPrometheusExporter] = None


def get_ai_quality_prometheus_exporter() -> AIQualityPrometheusExporter:
    """获取Prometheus导出器实例"""
    global _ai_quality_prometheus_exporter
    if _ai_quality_prometheus_exporter is None:
        _ai_quality_prometheus_exporter = AIQualityPrometheusExporter()
    return _ai_quality_prometheus_exporter


# ===================== Sentry集成 =====================

class AISentryIntegration:
    """
    AI质量监控Sentry集成

    功能：
    - 将AI对话记录为Sentry breadcrumb
    - 错误时自动捕获并上报到Sentry
    - 记录用户反馈到Sentry
    """

    def __init__(self):
        self._sentry_sdk = None
        self._initialized = False

    def initialize(self) -> None:
        """初始化Sentry集成"""
        try:
            import sentry_sdk
            self._sentry_sdk = sentry_sdk
            self._initialized = True
            logger.info("AI质量监控Sentry集成已初始化")
        except ImportError:
            logger.warning("Sentry SDK未安装，跳过AI质量监控Sentry集成")
            self._initialized = False

    def _add_breadcrumb(
        self,
        category: str,
        message: str,
        level: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """添加Sentry breadcrumb"""
        if not self._initialized or self._sentry_sdk is None:
            return

        try:
            self._sentry_sdk.add_breadcrumb(
                category=category,
                message=message,
                level=level,
                data=data or {},
            )
        except Exception as e:
            logger.warning(f"添加Sentry breadcrumb失败: {e}")

    def capture_conversation(
        self,
        request_id: str,
        session_id: Optional[str],
        user_id: Optional[int],
        message_length: int,
        response_length: int,
        response_time_ms: int,
        topics: Optional[List[str]] = None,
        tools_used: Optional[List[str]] = None,
        quality_score: Optional[int] = None,
    ) -> None:
        """记录AI对话到Sentry"""
        if not self._initialized:
            return

        self._add_breadcrumb(
            category="ai_conversation",
            message=f"AI对话完成: request_id={request_id}",
            level="info",
            data={
                "request_id": request_id,
                "session_id": session_id or "",
                "user_id": user_id or 0,
                "message_length": message_length,
                "response_length": response_length,
                "response_time_ms": response_time_ms,
                "topics": topics or [],
                "tools_used": tools_used or [],
                "quality_score": quality_score,
            },
        )

    def capture_error(
        self,
        request_id: str,
        session_id: Optional[str],
        user_id: Optional[int],
        error_type: str,
        response_time_ms: int,
        message_length: int,
    ) -> None:
        """记录AI错误到Sentry"""
        if not self._initialized:
            return

        self._add_breadcrumb(
            category="ai_error",
            message=f"AI对话错误: {error_type}",
            level="error",
            data={
                "request_id": request_id,
                "session_id": session_id or "",
                "user_id": user_id or 0,
                "error_type": error_type,
                "response_time_ms": response_time_ms,
                "message_length": message_length,
            },
        )

        # 捕获异常到Sentry
        try:
            if self._sentry_sdk is not None:
                self._sentry_sdk.capture_exception(
                    value=f"AI Error: {error_type}",
                    context={
                        "ai_quality": {
                            "request_id": request_id,
                            "session_id": session_id or "",
                            "user_id": user_id or 0,
                            "response_time_ms": response_time_ms,
                        }
                    },
                )
        except Exception as e:
            logger.warning(f"捕获Sentry异常失败: {e}")

    def capture_feedback(
        self,
        request_id: str,
        is_positive: bool,
        quality_score: Optional[int] = None,
        feedback_text: Optional[str] = None,
    ) -> None:
        """记录用户反馈到Sentry"""
        if not self._initialized:
            return

        level = "info" if is_positive else "warning"
        self._add_breadcrumb(
            category="ai_feedback",
            message=f"用户反馈: {'正面' if is_positive else '负面'}",
            level=level,
            data={
                "request_id": request_id,
                "is_positive": is_positive,
                "quality_score": quality_score,
                "feedback_text": feedback_text or "",
            },
        )


# 全局Sentry集成实例
_ai_sentry_integration: Optional[AISentryIntegration] = None


def get_ai_sentry_integration() -> AISentryIntegration:
    """获取AI Sentry集成实例"""
    global _ai_sentry_integration
    if _ai_sentry_integration is None:
        _ai_sentry_integration = AISentryIntegration()
        _ai_sentry_integration.initialize()
    return _ai_sentry_integration


# 示例：如何在AI咨询中使用
"""
from app.middleware.ai_quality_middleware import get_ai_logger, AILoggerService

# 在AI咨询完成后记录
logger = get_ai_logger()
logger.log_conversation(
    request_id=request_id,
    session_id=session_id,
    user_id=user_id,
    message_length=len(message),
    response_length=len(response),
    response_time_ms=response_time,
    quality_score=user_rating,  # 用户评分
    topics=["劳动法", "合同法"],
    tools_used=["calculator", "knowledge_search"],
)

# 在用户反馈时记录
logger.log_feedback(request_id=request_id, is_positive=True)

# 生产环境使用Redis版本
async def get_redis_ai_metrics(redis_client):
    metrics = await get_redis_ai_metrics(redis_client)
    # 定期持久化
    await metrics.persist_all()
"""


# 示例：如何在AI咨询中使用
"""
from app.middleware.ai_quality_middleware import get_ai_logger, AILoggerService

# 在AI咨询完成后记录
logger = get_ai_logger()
logger.log_conversation(
    request_id=request_id,
    session_id=session_id,
    user_id=user_id,
    message_length=len(message),
    response_length=len(response),
    response_time_ms=response_time,
    quality_score=user_rating,  # 用户评分
    topics=["劳动法", "合同法"],
    tools_used=["calculator", "knowledge_search"],
)

# 在用户反馈时记录
logger.log_feedback(request_id=request_id, is_positive=True)

# 生产环境使用Redis版本
async def get_redis_ai_metrics(redis_client):
    metrics = await get_redis_ai_metrics(redis_client)
    # 定期持久化
    await metrics.persist_all()
"""
