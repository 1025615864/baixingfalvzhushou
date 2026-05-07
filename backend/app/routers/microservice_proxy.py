"""Backend 微服务代理层

⚠️ Backend 作为 BFF 层，不直接处理业务逻辑。
⚠️ 所有请求通过此层代理到对应的微服务。
"""
from __future__ import annotations

import logging
from typing import Any
import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# 微服务路由表
MICROSERVICES: dict[str, dict[str, Any]] = {
    "user": {"prefix": "/users", "url": "${USER_SERVICE_URL:-http://user-service:8001}"},
    "legal": {"prefix": "/legal", "url": "${LEGAL_SERVICE_URL:-http://legal-service:8004}"},
    "ai": {"prefix": "/ai", "url": "${AI_SERVICE_URL:-http://ai-service:8005}"},
    "news": {"prefix": "/news", "url": "${NEWS_SERVICE_URL:-http://news-service:8006}"},
    "community": {"prefix": "/community", "url": "${COMMUNITY_SERVICE_URL:-http://community-service:8007}"},
    "points": {"prefix": "/points", "url": "${POINTS_SERVICE_URL:-http://points-service:8008}"},
    "notification": {"prefix": "/notifications", "url": "${NOTIFICATION_SERVICE_URL:-http://notification-service:8009}"},
    "recommendation": {"prefix": "/recommendations", "url": "${RECOMMENDATION_SERVICE_URL:-http://recommendation-service:8010}"},
    "search": {"prefix": "/search", "url": "${SEARCH_SERVICE_URL:-http://search-service:8011}"},
    "archive": {"prefix": "/archives", "url": "${ARCHIVE_SERVICE_URL:-http://archive-service:8012}"},
    "knowledge": {"prefix": "/knowledge", "url": "${KNOWLEDGE_SERVICE_URL:-http://knowledge-service:8013}"},
    "order": {"prefix": "/orders", "url": "${ORDER_SERVICE_URL:-http://order-service:8014}"},
    "embedding": {"prefix": "/embedding", "url": "${EMBEDDING_SERVICE_URL:-http://embedding-service:8015}"},
}


async def proxy_to_microservice(request: Request, service_name: str, path: str) -> Response:
    """代理请求到微服务"""
    service_url = _resolve_service_url(service_name)
    if not service_url:
        return JSONResponse(
            status_code=503,
            content={"error": "service_unavailable", "message": f"微服务 {service_name} 不可用"},
        )

    target_url = f"{service_url}/{path.lstrip('/')}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=_forward_headers(request),
                params=request.query_params,
                content=await request.body(),
                follow_redirects=False,
            )

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type"),
            )
        except httpx.ConnectError:
            logger.error(f"无法连接到微服务 {service_name}: {service_url}")
            return JSONResponse(
                status_code=503,
                content={"error": "service_unavailable", "message": f"微服务 {service_name} 连接失败"},
            )
        except Exception as e:
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
