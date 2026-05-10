"""错误率告警工具

监控错误率并触发告警。
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any, Optional

from app.utils.monitoring.error_classifier import ErrorCode, ErrorSeverity


logger = logging.getLogger(__name__)


class ErrorRateMonitor:
    """错误率监控器"""

    def __init__(
        self,
        window_seconds: int = 300,  # 5分钟窗口
        error_threshold: float = 0.01,  # 1%错误率阈值
        critical_threshold: float = 0.05  # 5%严重错误率阈值
    ) -> None:
        self.window_seconds = window_seconds
        self.error_threshold = error_threshold
        self.critical_threshold = critical_threshold

        self.error_counts: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.alerts: list[dict[str, Any]] = []

    def record_error(
        self,
        error_code: ErrorCode,
        error_message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: dict[str, Any] | None = None
    ) -> None:
        """记录错误

        Args:
            error_code: 错误码
            error_message: 错误消息
            severity: 错误严重程度
            context: 错误上下文
        """
        error_record = {
            "code": error_code.value,
            "message": error_message,
            "severity": severity.value,
            "timestamp": time.time(),
            "context": context or {},
        }

        self.error_counts[error_code.value].append(error_record)

        # 清理过期记录
        self._cleanup_old_records()

    def _cleanup_old_records(self) -> None:
        """清理过期记录"""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds

        for code in list(self.error_counts.keys()):
            self.error_counts[code] = [
                record for record in self.error_counts[code]
                if record["timestamp"] > cutoff_time
            ]

            if not self.error_counts[code]:
                del self.error_counts[code]

    def get_error_rate(
        self,
        window_seconds: int | None = None
    ) -> dict[str, Any]:
        """获取错误率

        Args:
            window_seconds: 时间窗口（秒）

        Returns:
            错误率统计
        """
        window = window_seconds or self.window_seconds
        current_time = time.time()
        cutoff_time = current_time - window

        total_errors = 0
        total_critical = 0

        for code, records in self.error_counts.items():
            valid_records = [
                record for record in records
                if record["timestamp"] > cutoff_time
            ]

            total_errors += len(valid_records)
            total_critical += sum(
                1 for record in valid_records
                if record["severity"] == "critical"
            )

        # 假设总请求数（实际应该从metrics获取）
        total_requests = max(total_errors * 10, 100)  # 避免除零

        error_rate = total_errors / total_requests
        critical_rate = total_critical / total_requests

        return {
            "total_errors": total_errors,
            "total_critical": total_critical,
            "total_requests": total_requests,
            "error_rate": error_rate,
            "critical_rate": critical_rate,
            "window_seconds": window,
        }

    def check_error_rate(self) -> Optional[dict[str, Any]]:
        """检查错误率并触发告警

        Returns:
            告警信息，如果没有告警则返回None
        """
        stats = self.get_error_rate()

        # 检查严重错误率
        if stats["critical_rate"] > self.critical_threshold:
            alert = {
                "level": "critical",
                "message": f"严重错误率过高: {stats['critical_rate']:.2%}",
                "error_rate": stats["critical_rate"],
                "threshold": self.critical_threshold,
                "timestamp": time.time(),
            }
            self.alerts.append(alert)
            logger.critical(f"CRITICAL: {alert['message']}")
            return alert

        # 检查普通错误率
        if stats["error_rate"] > self.error_threshold:
            alert = {
                "level": "warning",
                "message": f"错误率过高: {stats['error_rate']:.2%}",
                "error_rate": stats["error_rate"],
                "threshold": self.error_threshold,
                "timestamp": time.time(),
            }
            self.alerts.append(alert)
            logger.warning(f"WARNING: {alert['message']}")
            return alert

        return None

    def get_top_errors(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取最常见的错误

        Args:
            limit: 返回数量限制

        Returns:
            错误列表
        """
        error_counts = defaultdict(int)

        for code, records in self.error_counts.items():
            error_counts[code] = len(records)

        sorted_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {"code": code, "count": count}
            for code, count in sorted_errors[:limit]
        ]

    def get_alerts(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取告警列表

        Args:
            limit: 返回数量限制

        Returns:
            告警列表
        """
        return self.alerts[-limit:]


# 全局错误率监控器
error_rate_monitor = ErrorRateMonitor()


def record_error(
    error_code: ErrorCode,
    error_message: str,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    context: dict[str, Any] | None = None
) -> None:
    """记录错误（便捷函数）

    Args:
        error_code: 错误码
        error_message: 错误消息
        severity: 错误严重程度
        context: 错误上下文
    """
    error_rate_monitor.record_error(
        error_code, error_message, severity, context
    )


def check_error_rate() -> Optional[dict[str, Any]]:
    """检查错误率（便捷函数）

    Returns:
        告警信息，如果没有告警则返回None
    """
    return error_rate_monitor.check_error_rate()


# 错误率告警最佳实践
ERROR_RATE_ALERTING_BEST_PRACTICES = {
    "window_seconds": {
        "description": "时间窗口",
        "recommendation": "300秒",
        "reason": "5分钟窗口提供合理的错误率统计",
    },
    "error_threshold": {
        "description": "错误率阈值",
        "recommendation": "1%",
        "reason": "超过1%错误率需要关注",
    },
    "critical_threshold": {
        "description": "严重错误率阈值",
        "recommendation": "5%",
        "reason": "超过5%严重错误率需要立即处理",
    },
    "alert_notification": {
        "description": "告警通知",
        "recommendation": "邮件/短信/Slack",
        "reason": "及时通知运维人员",
    },
}
