"""中间件模块

统一导出所有中间件，包括：
- app/middleware/ 目录下的中间件
- app/core/middleware/ 目录下的核心中间件

使用示例:
    from app.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
"""
from .rate_limit import RateLimitMiddleware, ai_chat_limiter, document_limiter

# 重新导出 core/middleware 中的内容，保持向后兼容
from app.core.middleware import (
    LogSanitizer,
    sanitize_log_message,
    sanitize_dict_data,
    SecurityHeadersMiddleware,
    get_security_headers,
    SlowQueryLoggerMiddleware,
    SlowQueryRecorder,
    get_slow_query_recorder,
    PaymentIdempotencyService,
    PaymentProvider,
    IdempotencyStatus,
    IdempotencyResult,
    get_idempotency_service,
)

__all__ = [
    # 速率限制
    "RateLimitMiddleware",
    "ai_chat_limiter",
    "document_limiter",
    # 日志脱敏
    "LogSanitizer",
    "sanitize_log_message",
    "sanitize_dict_data",
    # 安全头
    "SecurityHeadersMiddleware",
    "get_security_headers",
    # 慢查询
    "SlowQueryLoggerMiddleware",
    "SlowQueryRecorder",
    "get_slow_query_recorder",
    # 支付幂等性
    "PaymentIdempotencyService",
    "PaymentProvider",
    "IdempotencyStatus",
    "IdempotencyResult",
    "get_idempotency_service",
]
