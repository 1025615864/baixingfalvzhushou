"""中间件配置模块"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_settings
from ..middleware.logging_middleware import RequestLoggingMiddleware, ErrorLoggingMiddleware
from ..middleware.auth_context_middleware import AuthContextMiddleware
from ..middleware.sentry_context_middleware import SentryContextMiddleware
from ..middleware.request_id_middleware import RequestIdMiddleware, TracingMiddleware
from ..middleware.rate_limit import RateLimitMiddleware
from ..middleware.metrics_middleware import MetricsMiddleware
from ..middleware.envelope_middleware import EnvelopeMiddleware
from ..middleware.ai_quality_middleware import AIQualityMiddleware
from ..middleware.csrf_middleware import csrf_middleware
from ..middleware.audit_middleware import AuditMiddleware
from .middleware import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)
settings = get_settings()


def setup_middlewares(app: FastAPI) -> None:
    """配置所有中间件（按执行顺序的逆序添加）"""
    
    # 1. 错误日志中间件（最先执行，最后返回）
    app.add_middleware(ErrorLoggingMiddleware)
    
    # 2. 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # 3. CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins or [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "accept",
            "accept-language",
            "authorization",
            "content-type",
            "content-language",
            "origin",
            "referer",
            "user-agent",
            "x-csrf-token",
            "x-request-id",
            "x-locale",
        ],
        max_age=600,
    )
    
    # 4. 速率限制中间件
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=120,
        requests_per_second=20,
        excluded_paths=[
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/health",
            "/",
            "/api/docs",
        ],
        trusted_proxies=settings.trusted_proxies,
    )
    
    # 5. 指标收集中间件
    app.add_middleware(MetricsMiddleware)
    
    # 6. 响应信封中间件
    app.add_middleware(EnvelopeMiddleware)
    
    # 7. 安全响应头中间件
    app.add_middleware(
        SecurityHeadersMiddleware,
        csp_mode="app",
        add_hsts=not settings.debug,
    )
    
    # 8. CSRF 中间件
    _ = app.middleware("http")(csrf_middleware)
    
    # 9. Sentry 上下文中间件
    app.add_middleware(SentryContextMiddleware)
    
    # 10. 认证上下文中间件
    app.add_middleware(AuthContextMiddleware)
    
    # 11. 审计中间件
    app.add_middleware(AuditMiddleware)
    
    # 12. 请求 ID 中间件（最后执行，最先返回）
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(TracingMiddleware)
    app.add_middleware(AIQualityMiddleware)
    
    logger.info("所有中间件配置完成")