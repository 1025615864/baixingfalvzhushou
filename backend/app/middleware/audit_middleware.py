"""API安全审计中间件

记录API访问日志、敏感操作审计日志、异常访问检测。
"""
from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.rate_limiter import get_client_ip
from ..services.audit_service import AuditAction, AuditSeverity, log_audit


class AuditMiddleware(BaseHTTPMiddleware):
    """安全审计中间件"""

    # 敏感操作列表
    SENSITIVE_OPERATIONS = {
        "DELETE",
        "admin",
        "payment",
        "user",
        "config",
    }

    # 异常访问阈值
    SUSPICIOUS_REQUESTS_THRESHOLD = 100  # 5分钟内超过100次请求
    SUSPICIOUS_ERRORS_THRESHOLD = 10     # 5分钟内超过10次错误

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._request_counts: dict[str, int] = {}
        self._error_counts: dict[str, int] = {}
        self._last_cleanup: float = time.time()

    def _cleanup_old_records(self) -> None:
        """清理过期记录"""
        current_time = time.time()
        if current_time - self._last_cleanup < 300:  # 5分钟清理一次
            return

        self._request_counts.clear()
        self._error_counts.clear()
        self._last_cleanup = current_time

    def _is_sensitive_operation(self, path: str) -> bool:
        """判断是否为敏感操作"""
        path_lower = path.lower()
        for sensitive in self.SENSITIVE_OPERATIONS:
            if sensitive in path_lower:
                return True
        return False

    def _detect_suspicious_access(
        self,
        ip: str,
        path: str,
        status_code: int
    ) -> bool:
        """检测异常访问"""
        self._cleanup_old_records()

        # 统计请求次数
        key = f"{ip}:{path}"
        self._request_counts[key] = self._request_counts.get(key, 0) + 1

        # 统计错误次数
        error_key = f"{ip}:{path}"
        if status_code >= 400:
            self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1

        # 检测异常
        if self._request_counts.get(key, 0) > self.SUSPICIOUS_REQUESTS_THRESHOLD:
            return True

        if self._error_counts.get(error_key, 0) > self.SUSPICIOUS_ERRORS_THRESHOLD:
            return True

        return False

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """处理请求"""
        start_time = time.time()
        path = request.url.path
        method = request.method
        ip = get_client_ip(request)

        # 检查是否为敏感操作
        is_sensitive = self._is_sensitive_operation(path)

        # 处理请求
        response = await call_next(request)

        # 记录审计日志
        duration = time.time() - start_time
        status_code = response.status_code

        # 检测异常访问
        is_suspicious = self._detect_suspicious_access(ip, path, status_code)

        # 构建审计日志
        audit_log = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ip": ip,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            "is_sensitive": is_sensitive,
            "is_suspicious": is_suspicious,
        }

        # 添加用户ID（如果存在）
        if hasattr(request.state, "user_id") and request.state.user_id:
            audit_log["user_id"] = request.state.user_id

        # 添加请求ID（如果存在）
        if hasattr(request.state, "request_id") and request.state.request_id:
            audit_log["request_id"] = request.state.request_id

        # 输出审计日志
        if is_sensitive or is_suspicious:
            severity = AuditSeverity.WARNING if is_suspicious else AuditSeverity.INFO
            try:
                log_audit(
                    action=AuditAction.API_CALL,
                    resource_type="http_request",
                    resource_id=path,
                    details=audit_log,
                    success=status_code < 400,
                    error_message=None if status_code < 400 else f"status_{status_code}",
                    severity=severity,
                    user_id=getattr(request.state, "user_id", None),
                    ip_address=ip,
                    request_id=getattr(request.state, "request_id", None),
                )
            except Exception:
                pass

        return response
