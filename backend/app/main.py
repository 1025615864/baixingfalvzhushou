"""百姓法律助手 - FastAPI主应用"""
import asyncio
from contextlib import asynccontextmanager
import logging
import os
from typing import Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from fastapi.exceptions import ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .config.sentry import init_sentry
from .database import init_db
from .services import cache_service, prometheus_metrics, periodic_jobs
from .services.ai_metrics import ai_metrics
from .services.sitemap_service import generate_robots_txt, generate_sitemap_xml
from .services.health_service import get_detailed_health
from .routers import api_router, websocket
from .middleware.logging_middleware import RequestLoggingMiddleware, ErrorLoggingMiddleware
from .middleware.auth_context_middleware import AuthContextMiddleware
from .middleware.sentry_context_middleware import SentryContextMiddleware
from .middleware.request_id_middleware import RequestIdMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.metrics_middleware import MetricsMiddleware
from .middleware.envelope_middleware import EnvelopeMiddleware
from .utils.periodic_task_runner import PeriodicLockedRunner

try:
    from services.common.tracing import init_telemetry
except ImportError:
    def init_telemetry(*args, **kwargs):
        pass

try:
    from services.common.discovery import get_consul_registry
except ImportError:
    def get_consul_registry(*args, **kwargs):
        return None

settings = get_settings()

logger = logging.getLogger(__name__)

init_sentry(settings)

try:
    from .routers import auth as auth_router
except Exception:
    auth_router = None
    logger.exception("认证路由加载失败")

try:
    from .routers import user_profile as user_router
except Exception:
    user_router = None
    logger.exception("用户路由加载失败")


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """应用生命周期管理"""
    _ = app

    consul = get_consul_registry()

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    init_telemetry(
        service_name="baixing-backend",
        service_version="1.0.0",
        otlp_endpoint=otlp_endpoint if otlp_endpoint else None,
    )
    logger.info("OpenTelemetry链路追踪已初始化")

    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        host = os.getenv("SERVICE_HOST", "localhost")
        port = int(os.getenv("SERVICE_PORT", "8080"))
        await consul.register_service(
            service_name="baixing-backend",
            service_id=f"baixing-backend-{port}",
            host=host,
            port=port,
            metadata={"version": "1.0.0", "environment": os.getenv("ENV", "development")},
            tags=["http", "api"],
            health_check_url=f"http://{host}:{port}/health",
        )
        logger.info(f"服务已注册到Consul: baixing-backend:{port}")

    await init_db()

    stop_event = asyncio.Event()

    runner = PeriodicLockedRunner(stop_event=stop_event, lock_client=cache_service.cache_service, logger=logger)

    redis_connected = False

    if settings.redis_url:
        redis_connected = bool(await cache_service.cache_service.connect(settings.redis_url))

    if (not settings.debug) and (not redis_connected):
        raise RuntimeError("Redis must be available when DEBUG is False. Please set REDIS_URL and ensure Redis is reachable.")

    periodic_tasks = periodic_jobs.setup_periodic_tasks(settings, runner, redis_connected)

    logger.info("数据库初始化完成")
    
    yield

    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        port = int(os.getenv("SERVICE_PORT", "8080"))
        await consul.deregister_service(f"baixing-backend-{port}")
        logger.info("服务已从Consul注销")

    stop_event.set()
    for t in periodic_tasks:
        _ = t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    await cache_service.cache_service.disconnect()

    logger.info("应用关闭")


app = FastAPI(
    title=settings.app_name,
    description="""
# 百姓法律助手 API

提供AI法律咨询、论坛交流、新闻资讯、律所查询等服务的RESTful API。

## 功能模块

- **👤 用户模块** - 注册、登录、个人信息管理
- **🤖 AI咨询** - 智能法律问答、会话管理
- **📰 新闻资讯** - 法律新闻浏览
- **💬 社区论坛** - 帖子发布、评论互动
- **🏢 律所服务** - 律所/律师查询、预约咨询
- **📄 文书生成** - 法律文书模板生成
- **🔍 全局搜索** - 跨模块搜索
- **⚙️ 系统管理** - 配置管理、数据统计

## 认证方式

使用 JWT Bearer Token 认证，在请求头中添加：
```
Authorization: Bearer <your_token>
```

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器错误 |
""",
    version="1.0.0",
    lifespan=lifespan,
    # 生产环境禁用API文档，开发环境启用
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_tags=[
        {"name": "用户管理", "description": "用户注册、登录、个人信息管理"},
        {"name": "AI法律助手", "description": "AI智能法律咨询"},
        {"name": "知识库管理", "description": "法律知识库与咨询模板管理"},
        {"name": "新闻资讯", "description": "法律新闻浏览"},
        {"name": "社区论坛", "description": "帖子发布、评论互动"},
        {"name": "律所服务", "description": "律所/律师查询"},
        {"name": "文书生成", "description": "法律文书模板生成"},
        {"name": "全局搜索", "description": "跨模块搜索"},
        {"name": "系统管理", "description": "配置管理、数据统计"},
        {"name": "文件上传", "description": "文件上传管理"},
        {"name": "通知管理", "description": "消息通知"},
        {"name": "支付管理", "description": "订单与支付"},
        {"name": "WebSocket", "description": "实时消息"},
        {"name": "管理后台", "description": "管理员功能"},
    ],
    contact={
        "name": "百姓法律助手团队",
        "email": "support@baixing-law.com",
    },
    license_info={
        "name": "MIT License",
    }
)

if settings.environment == "production":
    app.openapi_url = None
    app.docs_url = None
    app.redoc_url = None


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
    logger.exception("Response validation error path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": exc.errors() if settings.debug else "服务器错误"},
    )

# 中间件顺序（从上往下，后添加的先执行）:
# 1. ErrorLoggingMiddleware - 捕获所有错误
# 2. RequestLoggingMiddleware - 记录请求日志
# 3. CORSMiddleware - 处理跨域
# 4. RateLimitMiddleware - 速率限制
# 5. EnvelopeMiddleware - 响应统一包装
# 6. MetricsMiddleware - 收集指标（在包装之前，记录真实业务数据）
# 7. SentryContextMiddleware - Sentry 上下文
# 8. AuthContextMiddleware - 认证上下文
# 9. RequestIdMiddleware - 请求 ID

app.add_middleware(ErrorLoggingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-CSRF-Token", "X-Request-ID", "X-Trace-ID", "Accept"],
)

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=120,
    requests_per_second=20,
    excluded_paths=["/docs", "/redoc", "/openapi.json", "/health", "/api/health", "/", "/api/docs"],
    trusted_proxies=settings.trusted_proxies,
)

app.add_middleware(MetricsMiddleware)
app.add_middleware(EnvelopeMiddleware)

app.add_middleware(SentryContextMiddleware)
app.add_middleware(AuthContextMiddleware)

app.add_middleware(RequestIdMiddleware)

app.include_router(api_router, prefix="/api/v1")
app.include_router(websocket.router)

if auth_router is not None:
    app.include_router(auth_router.router, prefix="/api")

if user_router is not None:
    app.include_router(user_router.router, prefix="/api")


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt() -> PlainTextResponse:
    base_url = getattr(settings, "frontend_base_url", "") or ""
    content = generate_robots_txt(base_url)
    return PlainTextResponse(content=content, media_type="text/plain")


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml() -> Response:
    base_url = getattr(settings, "frontend_base_url", "") or ""
    xml = generate_sitemap_xml(base_url)
    return Response(content=xml, media_type="application/xml")


@app.get("/")
async def root() -> dict[str, str]:
    """根路由"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "message": "欢迎使用百姓法律助手API",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查"""
    return {"status": "healthy"}


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics_endpoint(request: Request) -> Response:
    token = os.getenv("METRICS_AUTH_TOKEN", "").strip()
    if token:
        auth = str(request.headers.get("Authorization") or "").strip()
        if auth != f"Bearer {token}":
            return PlainTextResponse(content="unauthorized\n", status_code=401)

    extra_lines = ai_metrics.render_prometheus()
    body = prometheus_metrics.render_prometheus(extra_lines=extra_lines)
    return PlainTextResponse(content=body, media_type="text/plain; version=0.0.4")


@app.get("/api/health")
async def api_health_check() -> dict[str, str]:
    """健康检查（API别名，兼容前端proxy）"""
    return {"status": "healthy"}


@app.get("/health/detailed")
async def health_check_detailed() -> dict[str, Any]:
    return await get_detailed_health(settings)
