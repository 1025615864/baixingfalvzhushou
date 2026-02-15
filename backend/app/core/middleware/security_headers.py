"""安全响应头中间件

添加HTTP安全响应头，防止常见安全漏洞。

响应头配置:
    - X-Content-Type-Options: 防止MIME类型嗅探
    - X-Frame-Options: 防止点击劫持
    - X-XSS-Protection: 旧版浏览器XSS保护
    - Strict-Transport-Security: 强制HTTPS
    - Content-Security-Policy: 内容安全策略
    - Referrer-Policy: 引用策略
    - Permissions-Policy: 权限策略

使用示例:
    ```python
    from app.core.middleware.security_headers import SecurityHeadersMiddleware

    app.add_middleware(SecurityHeadersMiddleware)
    ```

自定义配置:
    ```python
    from app.core.middleware.security_headers import get_security_headers

    headers = get_security_headers(
        hsts_max_age=31536000,
        csp_directives={"default-src": "'self'"}
    )
    ```
"""
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
try:
    from typing import override
except ImportError:
    from typing_extensions import override

logger = logging.getLogger(__name__)


def get_security_headers(
    hsts_max_age: int = 31536000,
    include_hsts: bool = True,
    csp_mode: str = "strict",
) -> dict[str, str]:
    """获取安全响应头配置

    Args:
        hsts_max_age: HSTS有效期（秒），默认1年
        include_hsts: 是否包含HSTS头
        csp_mode: CSP模式，可选值: 'strict', 'relaxed', 'custom'

    Returns:
        响应头字典
    """
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    if include_hsts:
        headers["Strict-Transport-Security"] = (
            f"max-age={hsts_max_age}; includeSubDomains; preload"
        )

    csp_policies: dict[str, dict[str, str]] = {
        "strict": {
            "default-src": "'self'",
            "script-src": "'self'",
            "style-src": "'self' 'unsafe-inline'",
            "img-src": "'self' data: https:",
            "font-src": "'self'",
            "connect-src": "'self'",
            "frame-ancestors": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
            "object-src": "'none'",
        },
        "app": {
            "default-src": "'self'",
            "script-src": "'self'",
            "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src": "'self' data: https: blob:",
            "font-src": "'self' data: https://fonts.gstatic.com",
            "connect-src": "'self' https: wss:",
            "frame-ancestors": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
            "object-src": "'none'",
        },
        "relaxed": {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src": "'self' 'unsafe-inline'",
            "img-src": "'self' data: https: blob:",
            "font-src": "'self' data:",
            "connect-src": "'self' https://",
            "frame-ancestors": "'self'",
            "base-uri": "'self'",
            "form-action": "'self'",
            "object-src": "'none'",
        },
    }

    if csp_mode in csp_policies:
        csp_parts: list[str] = []
        for directive, value in csp_policies[csp_mode].items():
            csp_parts.append(f"{directive} {value}")
        headers["Content-Security-Policy"] = "; ".join(csp_parts)
    elif csp_mode != "disabled":
        logger.warning("Unknown CSP mode: %s, using strict mode", csp_mode)
        csp_mode = "strict"

    return headers


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全响应头中间件

    为所有HTTP响应添加安全相关的响应头。

    配置选项:
        - exclude_paths: 排除的路径列表
        - hsts_max_age: HSTS有效期
        - csp_mode: CSP模式
        - add_hsts: 是否添加HSTS头

    默认排除路径:
        - /health
        - /metrics
        - /docs
        - /redoc
        - /openapi.json
    """

    DEFAULT_EXCLUDE_PATHS: set[str] = {
        "/health",
        "/health/",
        "/metrics",
        "/metrics/",
        "/docs",
        "/docs/",
        "/redoc",
        "/redoc/",
        "/openapi.json",
        "/favicon.ico",
    }

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: set[str] | None = None,
        hsts_max_age: int = 31536000,
        csp_mode: str = "strict",
        add_hsts: bool = True,
    ) -> None:
        super().__init__(app)
        self.exclude_paths: set[str] = exclude_paths or self.DEFAULT_EXCLUDE_PATHS
        self.headers: dict[str, str] = get_security_headers(
            hsts_max_age=hsts_max_age,
            include_hsts=add_hsts,
            csp_mode=csp_mode,
        )

    def should_add_headers(self, path: str) -> bool:
        """检查是否应该添加安全头

        Args:
            path: 请求路径

        Returns:
            是否添加
        """
        if path in self.exclude_paths:
            return False

        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path.rstrip("/")):
                return False

        return True

    @override
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """处理请求

        Args:
            request: FastAPI请求对象
            call_next: 下一个处理器

        Returns:
            HTTP响应
        """
        response = await call_next(request)

        if self.should_add_headers(request.url.path):
            for key, value in self.headers.items():
                response.headers[key] = value

        return response
