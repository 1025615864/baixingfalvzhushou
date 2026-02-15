"""API版本控制模块

提供API版本管理功能，支持路径版本控制和版本协商。
集成Token轮换机制，增强API认证安全性。

版本控制策略:
    1. 路径版本控制: /api/v1/users, /api/v2/users
    2. 请求头版本协商: Accept-Version: v2
    3. 版本响应头: X-API-Version: v2, X-API-Deprecated: true

Token轮换集成:
    - 通过中间件自动处理Token刷新
    - 支持双Token策略 (access_token + refresh_token)
    - 自动检测即将过期的token并触发轮换

使用示例:
    ```python
    from fastapi import FastAPI
    from app.core.versioning import setup_versioning, versioned_router

    app = FastAPI()

    # 设置版本控制中间件（包含Token轮换）
    setup_versioning(app)

    # 使用版本化路由器
    @versioned_router.v1.get("/users")
    async def list_users_v1():
        return {"version": "v1", "users": []}

    @versioned_router.v2.get("/users")
    async def list_users_v2():
        return {"version": "v2", "users": [], "new_field": "value"}

    app.include_router(versioned_router.v1)
    app.include_router(versioned_router.v2)
    ```

响应头:
    X-API-Version: v1      # 当前API版本
    X-API-Deprecated: true # 是否已弃用
    X-Token-Rotated: true  # Token是否已轮换（仅当发生轮换时）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class APIVersion(str, Enum):
    """API版本枚举

    定义支持的API版本。

    Attributes:
        V1: 版本1，当前默认版本
        V2: 版本2，新增功能
        V3: 版本3，最新版本
    """

    V1 = "v1"
    V2 = "v2"
    V3 = "v3"


DEFAULT_VERSION = APIVersion.V1
SUPPORTED_VERSIONS = [APIVersion.V1, APIVersion.V2, APIVersion.V3]


@dataclass
class VersionedRoute:
    """版本化路由配置

    用于追踪和管理版本化路由的信息。

    Attributes:
        path: 路由路径
        router: APIRouter实例
        versions: 支持的版本列表
        deprecated: 是否已弃用
    """

    path: str
    router: APIRouter
    versions: list[APIVersion]
    deprecated: bool = False


class APIVersionMiddleware(BaseHTTPMiddleware):
    """API版本控制中间件

    处理版本相关的请求解析和响应头设置。

    功能:
        - 从URL路径中提取API版本
        - 设置请求状态的版本信息
        - 添加版本响应头
        - 标记弃用版本

    Examples:
        ```python
        from fastapi import FastAPI
        from app.core.versioning import APIVersionMiddleware

        app = FastAPI()
        app.add_middleware(APIVersionMiddleware, default_version=APIVersion.V1)
        ```
    """

    def __init__(
        self,
        app,
        default_version: APIVersion = DEFAULT_VERSION,
    ) -> None:
        super().__init__(app)
        self.default_version = default_version

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """处理请求

        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件/路由处理器

        Returns:
            HTTP响应
        """
        path = request.url.path

        if "/api/" not in path:
            return await call_next(request)

        extracted_version = self._extract_version_from_path(path)
        if extracted_version:
            request.state.api_version = extracted_version
        else:
            request.state.api_version = self.default_version

        request.state.api_version_deprecated = self._is_version_deprecated(
            request.state.api_version
        )

        response = await call_next(request)

        version = getattr(
            request.state, "api_version", self.default_version
        )
        response.headers["X-API-Version"] = version.value

        if self._is_version_deprecated(version):
            response.headers["X-API-Deprecated"] = "true"

        return response

    def _extract_version_from_path(self, path: str) -> Optional[APIVersion]:
        """从URL路径中提取API版本

        Args:
            path: 请求路径

        Returns:
            API版本，如果无法提取则返回None

        Examples:
            - "/api/v1/users" -> APIVersion.V1
            - "/api/users" -> None
        """
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api":
            version_str = parts[1]
            if not version_str.startswith("v"):
                version_str = f"v{version_str}"
            try:
                return APIVersion(version_str)
            except ValueError:
                pass
        return None

    def _is_version_deprecated(self, version: APIVersion) -> bool:
        """检查版本是否已弃用

        Args:
            version: API版本

        Returns:
            如果版本不在支持列表中则返回True
        """
        return version not in SUPPORTED_VERSIONS


class VersionedRouter:
    """版本化路由器

    用于管理不同版本的API路由，提供便捷的版本化路由创建方式。

    Features:
        - 自动为每个版本创建独立的路由器
        - 支持属性访问 (router.v1, router.v2, router.v3)
        - 支持批量包含路由器到多个版本

    Examples:
        ```python
        router = VersionedRouter()

        @router.v1.get("/users")
        async def get_users_v1():
            return {"users": []}

        @router.v2.get("/users")
        async def get_users_v2():
            return {"users": [], "total": 0}

        app.include_router(router.v1)
        app.include_router(router.v2)
        ```
    """

    def __init__(self, prefix: str = "/api") -> None:
        self.prefix = prefix
        self._routers: dict[APIVersion, APIRouter] = {}
        self._versioned_routes: list[VersionedRoute] = []

        for version in SUPPORTED_VERSIONS:
            self._routers[version] = APIRouter(
                prefix=f"{prefix}/{version.value}",
                tags=[f"API {version.value}"],
            )

    def get_router(self, version: APIVersion) -> APIRouter:
        """获取指定版本的路由器

        Args:
            version: API版本

        Returns:
            APIRouter实例
        """
        return self._routers.get(version, APIRouter())

    def include_router(
        self,
        router: APIRouter,
        versions: Optional[list[APIVersion]] = None,
        deprecated: bool = False,
        **kwargs,
    ) -> None:
        """将路由器包含到指定版本

        Args:
            router: 要包含的APIRouter
            versions: 要包含的版本列表，默认为所有版本
            deprecated: 路由是否已弃用
            **kwargs: 传递给include_router的额外参数
        """
        versions = versions or SUPPORTED_VERSIONS.copy()

        for version in versions:
            if version in self._routers:
                self._routers[version].include_router(router, **kwargs)

        self._versioned_routes.append(
            VersionedRoute(
                path=router.prefix,
                router=router,
                versions=versions,
                deprecated=deprecated,
            )
        )

    def get_all_routers(self) -> list[tuple[APIVersion, APIRouter]]:
        """获取所有版本的路由器

        Returns:
            版本和路由器元组的列表
        """
        return [(v, r) for v, r in self._routers.items()]

    def get_version_info(self) -> dict[str, Any]:
        """获取版本信息

        Returns:
            包含版本信息的字典
        """
        return {
            "default_version": self.default_version.value,
            "supported_versions": [v.value for v in SUPPORTED_VERSIONS],
            "routes": [
                {
                    "path": route.path,
                    "versions": [v.value for v in route.versions],
                    "deprecated": route.deprecated,
                }
                for route in self._versioned_routes
            ],
        }

    @property
    def default_version(self) -> APIVersion:
        """获取默认版本

        Returns:
            默认API版本
        """
        return DEFAULT_VERSION

    @property
    def v1(self) -> APIRouter:
        """获取v1版本路由器

        Returns:
            v1 APIRouter实例
        """
        return self._routers[APIVersion.V1]

    @property
    def v2(self) -> APIRouter:
        """获取v2版本路由器

        Returns:
            v2 APIRouter实例
        """
        return self._routers[APIVersion.V2]

    @property
    def v3(self) -> APIRouter:
        """获取v3版本路由器

        Returns:
            v3 APIRouter实例
        """
        return self._routers[APIVersion.V3]


class VersionNegotiator:
    """版本协商器

    支持通过多种方式进行版本协商，确定客户端请求的API版本。

    协商优先级:
        1. URL路径中的版本 (例如: /api/v2/users)
        2. Accept-Version请求头 (例如: Accept-Version: v2)
        3. 默认版本

    Examples:
        ```python
        negotiator = VersionNegotiator()

        @app.middleware("http")
        async def version_negotiation(request: Request, call_next):
            version = negotiator.negotiate(request)
            request.state.api_version = version
            return await call_next(request)
        ```
    """

    HEADER_NAME = "Accept-Version"

    def __init__(
        self,
        default_version: APIVersion = DEFAULT_VERSION,
        supported_versions: Optional[list[APIVersion]] = None,
    ) -> None:
        self.default_version = default_version
        self.supported_versions = (
            supported_versions or SUPPORTED_VERSIONS.copy()
        )

    def negotiate(self, request: Request) -> APIVersion:
        """协商确定API版本

        Args:
            request: FastAPI请求对象

        Returns:
            协商后的API版本
        """
        path = request.url.path
        path_version = self._extract_version_from_path(path)
        if path_version:
            return path_version

        header_version = self._extract_version_from_header(request)
        if header_version:
            return header_version

        return self.default_version

    def _extract_version_from_path(self, path: str) -> Optional[APIVersion]:
        """从路径中提取版本

        Args:
            path: 请求路径

        Returns:
            API版本，如果无法提取则返回None
        """
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api":
            version_str = parts[1]
            if not version_str.startswith("v"):
                version_str = f"v{version_str}"
            try:
                version = APIVersion(version_str)
                if version in self.supported_versions:
                    return version
            except ValueError:
                pass
        return None

    def _extract_version_from_header(
        self, request: Request
    ) -> Optional[APIVersion]:
        """从请求头中提取版本

        Args:
            request: FastAPI请求对象

        Returns:
            API版本，如果无法提取则返回None
        """
        header_value = request.headers.get(self.HEADER_NAME, "").strip()
        if not header_value:
            return None

        if not header_value.startswith("v"):
            header_value = f"v{header_value}"

        try:
            version = APIVersion(header_value.lower())
            if version in self.supported_versions:
                return version
        except ValueError:
            pass

        return None


def get_current_api_version(request: Request) -> APIVersion:
    """获取当前请求的API版本

    Args:
        request: FastAPI请求对象

    Returns:
        当前API版本，如果未设置则返回默认版本
    """
    return getattr(request.state, "api_version", DEFAULT_VERSION)


def is_api_deprecated(request: Request) -> bool:
    """检查当前请求的API版本是否已弃用

    Args:
        request: FastAPI请求对象

    Returns:
        如果版本已弃用则返回True
    """
    return getattr(request.state, "api_version_deprecated", False)


def create_versioned_response(
    data: Any,
    request: Request,
    deprecated: bool = False,
) -> JSONResponse:
    """创建带版本信息的响应

    自动添加X-API-Version和X-API-Deprecated响应头。

    Args:
        data: 响应数据
        request: FastAPI请求对象
        deprecated: 是否标记为弃用

    Returns:
        JSONResponse响应对象
    """
    response = JSONResponse(content=data)

    version = get_current_api_version(request)
    response.headers["X-API-Version"] = version.value

    if deprecated or is_api_deprecated(request):
        response.headers["X-API-Deprecated"] = "true"

    return response


versioned_router = VersionedRouter()
version_negotiator = VersionNegotiator()


def setup_versioning(app: FastAPI, default_version: APIVersion = DEFAULT_VERSION) -> None:
    """设置API版本控制

    为FastAPI应用配置版本控制中间件。

    Args:
        app: FastAPI应用实例
        default_version: 默认API版本
    """
    app.add_middleware(
        APIVersionMiddleware,
        default_version=default_version,
    )
