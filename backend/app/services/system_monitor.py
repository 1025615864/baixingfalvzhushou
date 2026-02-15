"""增强监控系统

提供业务指标监控和告警功能。
"""

import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    description: str
    condition: Callable[["SystemMonitor"], bool]
    level: AlertLevel
    cooldown_seconds: int = 300  # 冷却时间
    enabled: bool = True


@dataclass
class Alert:
    """告警实例"""
    rule_name: str
    level: AlertLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


class SystemMonitor:
    """系统监控器

    收集和监控各种业务指标，包括：
    - API 响应时间
    - 错误率
    - 队列积压
    - 资源使用
    - 业务指标（用户活跃、转化率等）
    """

    def __init__(self):
        self._start_time = time.time()
        self._metrics: Dict[str, Any] = {}
        self._counters: Dict[str, int] = {}
        self._timers: Dict[str, deque[float]] = {}  # 使用 deque 限制大小
        self._alert_rules: List[AlertRule] = []
        self._alerts: List[Alert] = []
        self._alert_cooldowns: Dict[str, datetime] = {}

        # 初始化默认告警规则
        self._init_default_rules()

    def _init_default_rules(self):
        """初始化默认告警规则"""
        self._alert_rules = [
            AlertRule(
                name="high_error_rate",
                description="错误率过高",
                condition=lambda m: m.get_error_rate() > 0.05,  # 5%
                level=AlertLevel.WARNING,
                cooldown_seconds=300,
            ),
            AlertRule(
                name="slow_response",
                description="API 响应时间过长",
                condition=lambda m: m.get_p95_response_time() > 5.0,  # 5秒
                level=AlertLevel.WARNING,
                cooldown_seconds=60,
            ),
            AlertRule(
                name="very_slow_response",
                description="API 响应时间严重超时",
                condition=lambda m: m.get_p99_response_time() > 10.0,  # 10秒
                level=AlertLevel.ERROR,
                cooldown_seconds=120,
            ),
            AlertRule(
                name="high_latency_queue",
                description="AI 响应队列积压",
                condition=lambda m: m.get_queue_size("ai_response") > 100,
                level=AlertLevel.WARNING,
                cooldown_seconds=180,
            ),
            AlertRule(
                name="user_spike",
                description="用户活跃数异常激增",
                condition=lambda m: m.get_user_activity_spike() > 3.0,  # 3倍增长
                level=AlertLevel.INFO,
                cooldown_seconds=600,
            ),
        ]

    # 计数器操作
    def inc_counter(self, name: str, value: int = 1):
        """增加计数器"""
        self._counters[name] = self._counters.get(name, 0) + value

    def dec_counter(self, name: str, value: int = 1):
        """减少计数器"""
        self._counters[name] = max(0, self._counters.get(name, 0) - value)

    def get_counter(self, name: str) -> int:
        """获取计数器值"""
        return self._counters.get(name, 0)

    # 定时器操作
    def record_timer(self, name: str, value: float):
        """记录响应时间"""
        if name not in self._timers:
            self._timers[name] = deque(maxlen=1000)  # 保留最近1000条
        self._timers[name].append(value)

    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """获取定时器统计"""
        if name not in self._timers or not self._timers[name]:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0,
                    "max": 0, "p50": 0, "p95": 0, "p99": 0}

        values: List[float] = sorted(self._timers[name])
        n = len(values)

        return {
            "count": n,
            "sum": sum(values),
            "avg": sum(values) / n,
            "min": values[0],
            "max": values[-1],
            "p50": values[int(n * 0.5)],
            "p95": values[int(n * 0.95)],
            "p99": values[int(n * 0.99)],
        }

    # 便捷方法
    def record_api_response(self, endpoint: str,
                            duration: float, success: bool):
        """记录 API 响应"""
        self.record_timer(f"api.{endpoint}", duration)
        self.inc_counter(f"api.{endpoint}.total")
        if success:
            self.inc_counter(f"api.{endpoint}.success")
        else:
            self.inc_counter(f"api.{endpoint}.error")

    def record_ai_response(self, duration: float, tokens: int):
        """记录 AI 响应"""
        self.record_timer("ai.response", duration)
        self.inc_counter("ai.response.total")
        self.inc_counter("ai.response.tokens", tokens)

    def record_user_action(self, action: str, success: bool):
        """记录用户行为"""
        status = "success" if success else "failure"
        self.inc_counter(f"user.action.{action}.{status}")

    # 统计方法
    def get_error_rate(self) -> float:
        """获取错误率"""
        total = self.get_counter("api.total")
        errors = self.get_counter("api.error")
        if total == 0:
            return 0.0
        return errors / total

    def get_p95_response_time(self) -> float:
        """获取 P95 响应时间"""
        stats = self.get_timer_stats("api.total")
        return stats.get("p95", 0)

    def get_p99_response_time(self) -> float:
        """获取 P99 响应时间"""
        stats = self.get_timer_stats("api.total")
        return stats.get("p99", 0)

    def get_queue_size(self, queue_name: str) -> int:
        """获取队列大小"""
        return self.get_counter(f"queue.{queue_name}")

    def get_user_activity_spike(self) -> float:
        """获取用户活跃度峰值"""
        current = self.get_counter("user.active")
        baseline = self.get_counter("user.active.baseline")
        if baseline == 0:
            return 1.0
        return current / baseline

    def get_uptime_seconds(self) -> float:
        """获取运行时间"""
        return time.time() - self._start_time

    # 告警相关
    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self._alert_rules.append(rule)

    def check_alerts(self) -> List[Alert]:
        """检查告警规则"""
        alerts = []
        now = datetime.now()

        for rule in self._alert_rules:
            if not rule.enabled:
                continue

            # 检查冷却
            last_alert = self._alert_cooldowns.get(rule.name)
            if last_alert and (
                    now - last_alert).total_seconds() < rule.cooldown_seconds:
                continue

            # 检查条件
            try:
                if rule.condition(self):
                    alert = Alert(
                        rule_name=rule.name,
                        level=rule.level,
                        message=rule.description,
                    )
                    alerts.append(alert)  # pyright: ignore
                    self._alert_cooldowns[rule.name] = now
                    self._alerts.append(alert)
            except Exception:
                logger.exception(f"检查告警规则 {rule.name} 时出错")

        # 只保留最近100条告警
        self._alerts = self._alerts[-100:]

        return alerts  # pyright: ignore

    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """获取最近的告警"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [a for a in self._alerts if a.timestamp > cutoff]

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        error_rate = self.get_error_rate()
        p95 = self.get_p95_response_time()
        uptime = self.get_uptime_seconds()

        # 计算健康分数
        health_score = 100

        if error_rate > 0.01:
            health_score -= 20
        if error_rate > 0.05:
            health_score -= 30

        if p95 > 2.0:
            health_score -= 10
        if p95 > 5.0:
            health_score -= 20

        if uptime < 3600:  # 小于1小时
            health_score -= 10

        health_status = "healthy"
        if health_score < 60:
            health_status = "critical"
        elif health_score < 80:
            health_status = "degraded"

        return {
            "status": health_status,
            "score": health_score,
            "uptime_seconds": uptime,
            "uptime_formatted": self._format_duration(uptime),
            "error_rate": error_rate,
            "p95_response_time": p95,
            "p99_response_time": self.get_p99_response_time(),
            "active_users": self.get_counter("user.active"),
            "api_requests_total": self.get_counter("api.total"),
            "ai_responses_total": self.get_counter("ai.response.total"),
            "recent_alerts": len(self.get_recent_alerts()),
        }

    def _format_duration(self, seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{int(seconds)}s"
        if seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        if seconds < 86400:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"
        return f"{int(seconds // 86400)}d {int((seconds % 86400) // 3600)}h"

    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标汇总"""
        return {
            "health": self.get_health_status(),
            "api": {
                "total_requests": self.get_counter("api.total"),
                "success_rate": 1 - self.get_error_rate(),
                "response_time": self.get_timer_stats("api.total"),
            },
            "ai": {
                "total_responses": self.get_counter("ai.response.total"),
                "total_tokens": self.get_counter("ai.response.tokens"),
                "response_time": self.get_timer_stats("ai.response"),
            },
            "users": {
                "active": self.get_counter("user.active"),
                "registered": self.get_counter("user.registered"),
                "vip": self.get_counter("user.vip"),
            },
            "business": {
                "consultations": self.get_counter("business.consultation"),
                "documents_generated": self.get_counter("business.document"),
                "lawyer_bookings": self.get_counter("business.booking"),
                "posts_created": self.get_counter("business.post"),
            },
        }


# 全局监控器实例
_monitor: Optional[SystemMonitor] = None


def get_system_monitor() -> SystemMonitor:
    """获取系统监控器单例"""
    global _monitor
    if _monitor is None:
        _monitor = SystemMonitor()
    return _monitor


# 便捷函数
def record_api_metric(endpoint: str, duration: float, success: bool):
    """记录 API 指标的便捷函数"""
    get_system_monitor().record_api_response(endpoint, duration, success)


def record_business_metric(action: str, value: int = 1):
    """记录业务指标的便捷函数"""
    monitor = get_system_monitor()
    monitor.inc_counter(f"business.{action}", value)


def get_health_check() -> Dict[str, Any]:
    """获取健康检查结果"""
    return get_system_monitor().get_health_status()
