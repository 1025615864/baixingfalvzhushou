"""AI 服务指标收集 - Prometheus 指标导出

收集 AI 聊天请求、流式响应、错误计数等指标，
供 /metrics 端点导出给 Prometheus。
"""
import time
import threading
from typing import Any


class AiMetrics:
    """AI 服务指标收集器

    线程安全的指标计数器，用于跟踪:
    - 聊天请求总数
    - 流式请求总数
    - 错误总数 (按错误码和端点分组)
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._started_at = time.time()
        self._chat_requests_total = 0
        self._chat_stream_requests_total = 0
        self._errors_total = 0
        self._error_code_counts: dict[str, int] = {}
        self._endpoint_error_counts: dict[str, int] = {}

    def inc_chat_requests(self) -> None:
        """增加聊天请求计数"""
        with self._lock:
            self._chat_requests_total += 1

    def inc_chat_stream_requests(self) -> None:
        """增加流式请求计数"""
        with self._lock:
            self._chat_stream_requests_total += 1

    def inc_error(self, error_code: str = "unknown", endpoint: str = "unknown") -> None:
        """记录错误

        Args:
            error_code: 错误代码
            endpoint: 发生错误的端点路径
        """
        with self._lock:
            self._errors_total += 1
            self._error_code_counts[error_code] = (
                self._error_code_counts.get(error_code, 0) + 1
            )
            self._endpoint_error_counts[endpoint] = (
                self._endpoint_error_counts.get(endpoint, 0) + 1
            )

    def snapshot(self) -> dict[str, Any]:
        """获取当前指标快照

        Returns:
            包含所有指标值的字典
        """
        with self._lock:
            return {
                "started_at": self._started_at,
                "chat_requests_total": self._chat_requests_total,
                "chat_stream_requests_total": self._chat_stream_requests_total,
                "errors_total": self._errors_total,
                "error_code_counts": dict(self._error_code_counts),
                "endpoint_error_counts": dict(self._endpoint_error_counts),
            }

    def render_prometheus(self) -> list[str]:
        """渲染为 Prometheus 指标格式

        Returns:
            Prometheus 文本指标行列表
        """
        snap = self.snapshot()

        def _escape(value: str) -> str:
            s = str(value)
            s = s.replace("\\", "\\\\")
            s = s.replace('"', '\\"')
            s = s.replace("\n", "\\n")
            return s

        lines: list[str] = []

        lines.append("# HELP baixing_ai_started_at_seconds Unix timestamp when AiMetrics started")
        lines.append("# TYPE baixing_ai_started_at_seconds gauge")
        lines.append(f"baixing_ai_started_at_seconds {snap['started_at']}")

        lines.append("# HELP baixing_ai_chat_requests_total Total /ai/chat requests")
        lines.append("# TYPE baixing_ai_chat_requests_total counter")
        lines.append(f"baixing_ai_chat_requests_total {snap['chat_requests_total']}")

        lines.append("# HELP baixing_ai_chat_stream_requests_total Total /ai/chat_stream requests")
        lines.append("# TYPE baixing_ai_chat_stream_requests_total counter")
        lines.append(f"baixing_ai_chat_stream_requests_total {snap['chat_stream_requests_total']}")

        lines.append("# HELP baixing_ai_errors_total Total AI errors")
        lines.append("# TYPE baixing_ai_errors_total counter")
        lines.append(f"baixing_ai_errors_total {snap['errors_total']}")

        lines.append("# HELP baixing_ai_error_code_total Total errors grouped by error_code")
        lines.append("# TYPE baixing_ai_error_code_total counter")
        for code in sorted(snap["error_code_counts"].keys()):
            v = snap["error_code_counts"][code]
            if v <= 0:
                continue
            lines.append(f'baixing_ai_error_code_total{{error_code="{_escape(code)}"}} {v}')

        lines.append("# HELP baixing_ai_endpoint_error_total Total errors grouped by endpoint")
        lines.append("# TYPE baixing_ai_endpoint_error_total counter")
        for ep in sorted(snap["endpoint_error_counts"].keys()):
            v = snap["endpoint_error_counts"][ep]
            if v <= 0:
                continue
            lines.append(f'baixing_ai_endpoint_error_total{{endpoint="{_escape(ep)}"}} {v}')

        return lines


# 全局单例
ai_metrics = AiMetrics()
