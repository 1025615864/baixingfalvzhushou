"""管理后台统一代理路由

将 /api/v1/admin/{service}/{path} 代理到对应微服务的管理接口，
在代理层统一校验管理员权限。
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from ..utils.security import decode_access_token
from ..utils.permissions import Role

logger = logging.getLogger(__name__)

ADMIN_SERVICES: dict[str, dict[str, Any]] = {
    "users": {"url": "${ADMIN_USER_SERVICE_URL:-http://localhost:8001}", "prefix": "/api/v1/admin"},
    "notifications": {"url": "${ADMIN_NOTIFICATION_SERVICE_URL:-http://localhost:8005}", "prefix": "/api/v1/admin"},
    "orders": {"url": "${ADMIN_ORDER_SERVICE_URL:-http://localhost:8008}", "prefix": "/api/v1/admin"},
    "payments": {"url": "${ADMIN_PAYMENT_SERVICE_URL:-http://localhost:8010}", "prefix": "/api/v1/payment/admin"},
    "accounting": {"url": "${ADMIN_ACCOUNTING_SERVICE_URL:-http://localhost:8014}", "prefix": "/api/v1/admin"},
    "knowledge": {"url": "${ADMIN_KNOWLEDGE_SERVICE_URL:-http://localhost:8081}", "prefix": "/api/v1/admin"},
    "archive": {"url": "${ADMIN_ARCHIVE_SERVICE_URL:-http://localhost:8012}", "prefix": "/api/v1/admin"},
    "embedding": {"url": "${ADMIN_EMBEDDING_SERVICE_URL:-http://localhost:8013}", "prefix": "/api/v1/admin"},
    "news": {"url": "${ADMIN_NEWS_SERVICE_URL:-http://localhost:8006}", "prefix": "/api/v1/news/admin"},
    "community": {"url": "${ADMIN_COMMUNITY_SERVICE_URL:-http://localhost:8003}", "prefix": "/api/v1/community/admin"},
    "legal": {"url": "${ADMIN_LEGAL_SERVICE_URL:-http://localhost:8002}", "prefix": "/api/v1/legal/admin"},
}

TIMEOUT_CONNECT = 5.0
TIMEOUT_READ = 30.0
TIMEOUT_WRITE = 60.0
TIMEOUT_STREAM = 300.0

ADMIN_ROLES = {Role.ADMIN, Role.SUPER_ADMIN}
GLOBAL_ROLES = {Role.SUPER_ADMIN, Role.ADMIN}

SERVICE_DOMAIN_MAP: dict[str, str] = {
    "users": "global",
    "legal": "legal",
    "news": "news",
    "community": "community",
    "orders": "order",
    "payments": "payment",
    "accounting": "payment",
    "knowledge": "knowledge",
    "archive": "archive",
    "notifications": "notification",
    "embedding": "embedding",
}


class _CircuitState:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class _CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = _CircuitState.CLOSED
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        if self.state == _CircuitState.CLOSED:
            return True
        if self.state == _CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = _CircuitState.HALF_OPEN
                return True
            return False
        return True

    def record_success(self):
        self.failure_count = 0
        self.state = _CircuitState.CLOSED

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = _CircuitState.OPEN
            logger.warning("Admin proxy circuit breaker opened after %d failures", self.failure_count)


_circuit_breakers: dict[str, _CircuitBreaker] = {
    name: _CircuitBreaker(failure_threshold=5, recovery_timeout=30)
    for name in ADMIN_SERVICES
}

router = APIRouter(tags=["admin-proxy"])


def _resolve_service_url(service_name: str) -> str | None:
    service = ADMIN_SERVICES.get(service_name)
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


def _verify_admin_token(request: Request, service_name: str | None = None) -> JSONResponse | dict[str, Any]:
    auth = str(request.headers.get("authorization") or "").strip()
    if not auth.lower().startswith("bearer "):
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized", "message": "未提供认证凭证"},
        )

    token = auth.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    if payload is None:
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized", "message": "无效的认证凭证"},
        )

    role = str(payload.get("role") or "").strip()
    domain = str(payload.get("domain") or "").strip()
    scope_id = str(payload.get("scope_id") or payload.get("domain_scope_id") or "").strip()

    if role not in ADMIN_ROLES:
        logger.warning("Admin proxy access denied: role=%s", role)
        return JSONResponse(
            status_code=403,
            content={"error": "forbidden", "message": "需要管理员权限"},
        )

    if service_name and role not in GLOBAL_ROLES:
        required_domain = SERVICE_DOMAIN_MAP.get(service_name)
        if required_domain and required_domain != "global":
            if not domain or domain != required_domain:
                logger.warning(
                    "Admin proxy domain check denied: role=%s domain=%s required_domain=%s service=%s",
                    role, domain, required_domain, service_name,
                )
                return JSONResponse(
                    status_code=403,
                    content={"error": "forbidden", "message": f"无权访问 {service_name} 服务的管理接口（需要 {required_domain} 域权限）"},
                )

    return {"role": role, "domain": domain, "scope_id": scope_id}


def _forward_headers(request: Request, admin_info: dict[str, Any] | None = None) -> dict[str, str]:
    headers: dict[str, str] = {}
    for key, value in request.headers.items():
        lk = key.lower()
        if lk in (
            "authorization",
            "content-type",
            "x-request-id",
            "x-trace-id",
            "x-correlation-id",
            "accept",
            "x-user-id",
            "x-user-role",
            "x-internal-api-key",
        ):
            headers[key] = value

    if admin_info:
        if admin_info.get("role"):
            headers["X-Admin-Role"] = admin_info["role"]
        if admin_info.get("domain"):
            headers["X-Admin-Domain"] = admin_info["domain"]
        if admin_info.get("scope_id"):
            headers["X-Admin-Scope-Id"] = admin_info["scope_id"]

    return headers


async def _proxy_to_admin_service(request: Request, service_name: str, path: str) -> Response:
    auth_result = _verify_admin_token(request, service_name)
    if isinstance(auth_result, JSONResponse):
        return auth_result

    admin_info = auth_result

    cb = _circuit_breakers.get(service_name)
    if cb and not cb.can_execute():
        return JSONResponse(
            status_code=503,
            content={
                "error": "circuit_open",
                "message": f"管理服务 {service_name} 暂时不可用（熔断器已打开）",
                "retry_after": cb.recovery_timeout,
            },
        )

    service_url = _resolve_service_url(service_name)
    if not service_url:
        return JSONResponse(
            status_code=503,
            content={"error": "service_unavailable", "message": f"管理服务 {service_name} 未配置"},
        )

    service_prefix = ADMIN_SERVICES[service_name]["prefix"]
    target_url = f"{service_url}{service_prefix}/{path.lstrip('/')}"

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
                        headers=_forward_headers(request, admin_info),
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
                headers=_forward_headers(request, admin_info),
                params=request.query_params,
                content=await request.body(),
                follow_redirects=False,
            )

            if cb:
                cb.record_success()

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type"),
            )
        except httpx.ConnectTimeout:
            if cb:
                cb.record_failure()
            logger.error("连接管理服务 %s 超时: %s", service_name, service_url)
            return JSONResponse(
                status_code=504,
                content={"error": "gateway_timeout", "message": f"管理服务 {service_name} 连接超时"},
            )
        except httpx.ReadTimeout:
            logger.error("读取管理服务 %s 响应超时: %s", service_name, service_url)
            return JSONResponse(
                status_code=504,
                content={"error": "gateway_timeout", "message": f"管理服务 {service_name} 响应超时"},
            )
        except httpx.ConnectError:
            if cb:
                cb.record_failure()
            logger.error("无法连接到管理服务 %s: %s", service_name, service_url)
            return JSONResponse(
                status_code=503,
                content={"error": "service_unavailable", "message": f"管理服务 {service_name} 连接失败"},
            )
        except Exception as e:
            if cb:
                cb.record_failure()
            logger.exception("管理代理请求失败: %s/%s", service_name, path)
            return JSONResponse(
                status_code=502,
                content={"error": "proxy_error", "message": str(e)},
            )


@router.api_route("/admin/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def admin_proxy(request: Request, service: str, path: str):
    if service not in ADMIN_SERVICES:
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "message": f"未知管理服务: {service}"},
        )
    return await _proxy_to_admin_service(request, service, path)


@router.get("/admin/proxy/circuit-status")
async def get_admin_circuit_breaker_status():
    status = {}
    for name, cb in _circuit_breakers.items():
        service = ADMIN_SERVICES[name]
        status[name] = {
            "state": cb.state,
            "failure_count": cb.failure_count,
            "threshold": cb.failure_threshold,
            "url": service["url"],
        }
    return {"circuit_breakers": status}
