"""Backend 微服务代理层

⚠️ Backend 作为 BFF 层，不直接处理业务逻辑。
⚠️ 所有请求通过此层代理到对应的微服务。
"""
from __future__ import annotations

import logging
import time
from typing import Any
import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

logger = logging.getLogger(__name__)

# 微服务路由表
# ⚠️ 端口必须与 docker-compose.yml 中的配置保持一致
MICROSERVICES: dict[str, dict[str, Any]] = {
    "user": {"prefix": "/users", "url": "${USER_SERVICE_URL:-http://user-service:8001}"},
    "payment-channel": {"prefix": "/payment", "url": "${PAYMENT_CHANNEL_SERVICE_URL:-http://payment-channel-service:8002}"},
    "embedding": {"prefix": "/embeddings", "url": "${EMBEDDING_SERVICE_URL:-http://embedding-service:8003}"},
    "order": {"prefix": "/orders", "url": "${ORDER_SERVICE_URL:-http://order-service:8004}"},
    "ai": {"prefix": "/ai", "url": "${AI_SERVICE_URL:-http://ai-service:8005}"},
    "notification": {"prefix": "/notifications", "url": "${NOTIFICATION_SERVICE_URL:-http://notification-service:8011}"},
    "news": {"prefix": "/news", "url": "${NEWS_SERVICE_URL:-http://news-service:8006}"},
    "community": {"prefix": "/community", "url": "${COMMUNITY_SERVICE_URL:-http://community-service:8007}"},
    "legal": {"prefix": "/legal", "url": "${LEGAL_SERVICE_URL:-http://legal-service:8008}"},
    "search": {"prefix": "/search", "url": "${SEARCH_SERVICE_URL:-http://search-service:8009}"},
    "recommendation": {"prefix": "/recommendation", "url": "${RECOMMENDATION_SERVICE_URL:-http://recommendation-service:8010}"},
    "points": {"prefix": "/points", "url": "${POINTS_SERVICE_URL:-http://points-service:8012}"},
    "archive": {"prefix": "/archive", "url": "${ARCHIVE_SERVICE_URL:-http://archive-service:8013}"},
    "knowledge": {"prefix": "/knowledge", "url": "${KNOWLEDGE_SERVICE_URL:-http://knowledge-service:8081}"},
    "payment-accounting": {"prefix": "/accounting", "url": "${PAYMENT_ACCOUNTING_SERVICE_URL:-http://payment-accounting-service:8014}"},

    # === 子路由代理（功能前缀与服务默认前缀不同）===
    "user-membership": {"prefix": "/membership", "url": "${USER_SERVICE_URL:-http://user-service:8001}"},
    "accounting-settlement": {"prefix": "/settlement", "url": "${PAYMENT_ACCOUNTING_SERVICE_URL:-http://payment-accounting-service:8014}"},
    "knowledge-court-cases": {"prefix": "/court-cases", "url": "${KNOWLEDGE_SERVICE_URL:-http://knowledge-service:8007}"},
}

# 超时配置（秒）
TIMEOUT_CONNECT = 5.0
TIMEOUT_READ = 30.0
TIMEOUT_WRITE = 60.0
TIMEOUT_STREAM = 300.0

# 熔断器状态
class CircuitState:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

# 简单的熔断器实现
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN allows one request

    def record_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

# 为每个微服务创建熔断器
_circuit_breakers: dict[str, CircuitBreaker] = {
    name: CircuitBreaker(failure_threshold=5, recovery_timeout=30)
    for name in MICROSERVICES
}

# 代理路由器
router = APIRouter(tags=["proxy"])


async def proxy_to_microservice(request: Request, service_name: str, path: str) -> Response:
    """代理请求到微服务（带熔断和超时控制）"""
    # 检查熔断器状态
    circuit_breaker = _circuit_breakers.get(service_name)
    if circuit_breaker and not circuit_breaker.can_execute():
        return JSONResponse(
            status_code=503,
            content={
                "error": "circuit_open",
                "message": f"微服务 {service_name} 暂时不可用（熔断器已打开）",
                "retry_after": circuit_breaker.recovery_timeout,
            },
        )

    service_url = _resolve_service_url(service_name)
    if not service_url:
        return JSONResponse(
            status_code=503,
            content={"error": "service_unavailable", "message": f"微服务 {service_name} 未配置"},
        )

    service_prefix = MICROSERVICES[service_name]["prefix"]
    target_url = f"{service_url}/api/v1{service_prefix}/{path.lstrip('/')}"

    # 根据请求方法选择不同的超时
    if request.method in ("POST", "PUT", "PATCH"):
        timeout = httpx.Timeout(connect=TIMEOUT_CONNECT, read=TIMEOUT_WRITE, write=TIMEOUT_WRITE, pool=TIMEOUT_CONNECT)
    else:
        timeout = httpx.Timeout(connect=TIMEOUT_CONNECT, read=TIMEOUT_READ, write=TIMEOUT_READ, pool=TIMEOUT_CONNECT)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            accept_header = request.headers.get("accept", "")
            is_stream = "text/event-stream" in accept_header

            if is_stream:
                stream_timeout = httpx.Timeout(connect=TIMEOUT_CONNECT, read=TIMEOUT_STREAM, write=TIMEOUT_WRITE, pool=TIMEOUT_CONNECT)

                async def stream_response():
                    async with client.stream(
                        method=request.method,
                        url=target_url,
                        headers=_forward_headers(request),
                        params=request.query_params,
                        content=await request.body(),
                        timeout=stream_timeout,
                    ) as resp:
                        async for chunk in resp.aiter_bytes():
                            yield chunk

                return StreamingResponse(
                    stream_response(),
                    status_code=200,
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                    },
                )

            response = await client.request(
                method=request.method,
                url=target_url,
                headers=_forward_headers(request),
                params=request.query_params,
                content=await request.body(),
                follow_redirects=False,
            )

            # 请求成功，记录成功
            if circuit_breaker:
                circuit_breaker.record_success()

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type"),
            )
        except httpx.ConnectTimeout:
            if circuit_breaker:
                circuit_breaker.record_failure()
            logger.error(f"连接微服务 {service_name} 超时: {service_url}")
            return JSONResponse(
                status_code=504,
                content={"error": "gateway_timeout", "message": f"微服务 {service_name} 连接超时"},
            )
        except httpx.ReadTimeout:
            logger.error(f"读取微服务 {service_name} 响应超时: {service_url}")
            return JSONResponse(
                status_code=504,
                content={"error": "gateway_timeout", "message": f"微服务 {service_name} 响应超时"},
            )
        except httpx.ConnectError:
            if circuit_breaker:
                circuit_breaker.record_failure()
            logger.error(f"无法连接到微服务 {service_name}: {service_url}")
            auth_header = request.headers.get("Authorization", "")
            if not auth_header:
                return JSONResponse(
                    status_code=401,
                    content={"error": "unauthorized", "message": "未授权访问"},
                )
            return JSONResponse(
                status_code=503,
                content={"error": "service_unavailable", "message": f"微服务 {service_name} 连接失败"},
            )
        except Exception as e:
            if circuit_breaker:
                circuit_breaker.record_failure()
            logger.exception(f"代理请求失败: {service_name}/{path}")
            return JSONResponse(
                status_code=502,
                content={"error": "proxy_error", "message": str(e)},
            )


def _resolve_service_url(service_name: str) -> str | None:
    """解析微服务URL"""
    import os

    service = MICROSERVICES.get(service_name)
    if not service:
        return None

    url_var = service["url"]

    if url_var.startswith("${") and url_var.endswith("}"):
        env_var = url_var[2:-1]
        parts = env_var.split(":-", 1)
        if len(parts) == 2:
            return os.getenv(parts[0], parts[1])
        return os.getenv(env_var)

    return url_var


def _forward_headers(request: Request) -> dict[str, str]:
    """转发必要的请求头"""
    forward_headers = {}
    for key, value in request.headers.items():
        if key.lower() in (
            "authorization", "content-type", "x-request-id",
            "x-trace-id", "x-correlation-id", "accept",
            "x-user-id", "x-user-role",
        ):
            forward_headers[key] = value
    return forward_headers


def create_proxy_router(service_name: str) -> APIRouter:
    """为微服务创建代理路由器"""
    service = MICROSERVICES[service_name]
    router = APIRouter(prefix=service["prefix"], tags=[f"{service_name}-service"])

    @router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy(request: Request, path: str):
        return await proxy_to_microservice(request, service_name, path)

    return router


@router.get("/proxy/circuit-status")
async def get_circuit_breaker_status():
    """获取所有微服务熔断器状态"""
    status = {}
    for name, cb in _circuit_breakers.items():
        service = MICROSERVICES[name]
        status[name] = {
            "state": cb.state,
            "failure_count": cb.failure_count,
            "threshold": cb.failure_threshold,
            "url": service["url"],
        }
    return {"circuit_breakers": status}
