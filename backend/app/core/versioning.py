"""API版本控制模块

提供API版本管理功能，支持路径版本控制和版本协商。
集成Token轮换机制，增强API认证安全性。

版本控制策略:
    1. 路径版本控制: /api/v1/users, /api/v2/users
    2. 请求头版本协商:
       - Accept-Version: v2
       - X-API-Version: v2
    3. 版本响应头:
       - X-API-Version: v2
       - X-API-Deprecated: true
       - X-API-Sunset: Sat, 01 Jan 2027 00:00:00 GMT
       - X-API-Latest-Version: v3
       - Link: </api/v3/users>; rel="successor-version"

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
    X-API-Sunset: ...      # 废弃日期（仅当版本已废弃时）
    X-Token-Rotated: true  # Token是否已轮换（仅当发生轮换时）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# ============================================================================
# 版本废弃配置
# ============================================================================

# 废弃版本配置：定义每个废弃版本的详细信息
DEPRECATED_VERSIONS_CONFIG: dict[str, dict[str, Any]] = {
    # 示例：当 v1 被废弃时取消注释
    # "v1": {
    #     "sunset_date": "2027-01-01T00:00:00Z",
    #     "successor_version": "v2",
    #     "deprecation_message": "API v1 已废弃，请迁移到 v2",
    # },
}


@dataclass
class VersionInfo:
    """版本信息
    
    包含版本的详细元数据信息。
    
    Attributes:
        version: 版本标识符
        is_deprecated: 是否已废弃
        sunset_date: 废弃日期（RFC 7231 格式）
        successor_version: 接替版本
        deprecation_message: 废弃提示信息
    """
    
    version: str
    is_deprecated: bool = False
    sunset_date: Optional[str] = None
    successor_version: Optional[str] = None
    deprecation_message: Optional[str] = None
    
    def to_response_headers(self, request_path: str = "") -> dict[str, str]:
        """生成响应头
        
        Args:
            request_path: 请求路径，用于生成 Link 头
        
        Returns:
            响应头字典
        """
        headers = {}
        
        if self.is_deprecated:
            headers["X-API-Deprecated"] = "true"
            
            if self.sunset_date:
                headers["X-API-Sunset"] = self.sunset_date
            
            if self.successor_version:
                headers["X-API-Latest-Version"] = self.successor_version
                
                # 生成 Link 头（RFC 8288）
                if request_path:
                    # 构建接替版本的 URL
                    path_parts = request_path.strip("/").split("/")
                    if len(path_parts) >= 2 and path_parts[0] == "api":
                        successor_path = f"/api/{self.successor_version}/{'/'.join(path_parts[2:])}"
                        headers["Link"] = f'<{successor_path}>; rel="successor-version"'
            
            if self.deprecation_message:
                # 使用 Warning 头传递废弃消息
                headers["Warning"] = f'299 - "{self.deprecation_message}"'
        
        return headers


@dataclass
class VersionCompatibilityResult:
    """版本兼容性检查结果
    
    Attributes:
        is_compatible: 是否兼容
        requested_version: 请求的版本
        effective_version: 实际生效的版本
        warnings: 警告信息列表
        migration_guide: 迁移指南 URL
    """
    
    is_compatible: bool
    requested_version: str
    effective_version: str
    warnings: list[str] = field(default_factory=list)
    migration_guide: Optional[str] = None


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
        - 从请求头中提取API版本（Accept-Version, X-API-Version）
        - 设置请求状态的版本信息
        - 添加版本响应头（X-API-Version, X-API-Deprecated, X-API-Sunset 等）
        - 标记弃用版本
        - 添加废弃警告信息

    响应头说明:
        - X-API-Version: 当前请求使用的API版本
        - X-API-Deprecated: 如果版本已废弃则为 "true"
        - X-API-Sunset: 废弃日期（RFC 7231 格式）
        - X-API-Latest-Version: 最新可用版本
        - X-API-Supported-Versions: 支持的版本列表
        - Link: RFC 8288 格式的接替版本链接
        - Warning: 废弃警告信息

    Examples:
        ```python
        from fastapi import FastAPI
        from app.core.versioning import APIVersionMiddleware

        app = FastAPI()
        app.add_middleware(APIVersionMiddleware, default_version=APIVersion.V1)
        ```
    """

    # 支持的版本协商请求头
    VERSION_HEADERS = ["Accept-Version", "X-API-Version"]

    def __init__(
        self,
        app,
        default_version: APIVersion = DEFAULT_VERSION,
        include_supported_versions_header: bool = True,
    ) -> None:
        super().__init__(app)
        self.default_version = default_version
        self.include_supported_versions_header = include_supported_versions_header

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

        # 版本协商优先级：URL路径 > X-API-Version > Accept-Version > 默认版本
        extracted_version = self._extract_version_from_path(path)
        if not extracted_version:
            extracted_version = self._extract_version_from_headers(request)
        
        if extracted_version:
            request.state.api_version = extracted_version
        else:
            request.state.api_version = self.default_version

        # 获取版本信息
        version_info = self._get_version_info(request.state.api_version)
        request.state.api_version_deprecated = version_info.is_deprecated
        request.state.api_version_info = version_info

        response = await call_next(request)

        # 设置版本响应头
        version = getattr(
            request.state, "api_version", self.default_version
        )
        response.headers["X-API-Version"] = version.value

        # 添加支持的版本列表
        if self.include_supported_versions_header:
            response.headers["X-API-Supported-Versions"] = ", ".join(
                v.value for v in SUPPORTED_VERSIONS
            )

        # 添加废弃相关响应头
        deprecation_headers = version_info.to_response_headers(path)
        for header_name, header_value in deprecation_headers.items():
            response.headers[header_name] = header_value

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

    def _extract_version_from_headers(self, request: Request) -> Optional[APIVersion]:
        """从请求头中提取API版本

        支持的请求头：
            - X-API-Version: v2
            - Accept-Version: v2

        优先级：X-API-Version > Accept-Version

        Args:
            request: FastAPI请求对象

        Returns:
            API版本，如果无法提取则返回None
        """
        for header_name in self.VERSION_HEADERS:
            header_value = request.headers.get(header_name, "").strip()
            if not header_value:
                continue

            # 标准化版本字符串
            if not header_value.startswith("v"):
                header_value = f"v{header_value}"

            try:
                version = APIVersion(header_value.lower())
                # 只返回支持的版本
                if version in SUPPORTED_VERSIONS:
                    return version
            except ValueError:
                logger.debug(
                    f"无效的版本头 {header_name}: {header_value}"
                )
        
        return None

    def _get_version_info(self, version: APIVersion) -> VersionInfo:
        """获取版本的详细信息

        Args:
            version: API版本

        Returns:
            VersionInfo 实例
        """
        version_str = version.value
        
        # 检查是否在废弃配置中
        if version_str in DEPRECATED_VERSIONS_CONFIG:
            config = DEPRECATED_VERSIONS_CONFIG[version_str]
            return VersionInfo(
                version=version_str,
                is_deprecated=True,
                sunset_date=config.get("sunset_date"),
                successor_version=config.get("successor_version"),
                deprecation_message=config.get("deprecation_message"),
            )
        
        # 检查是否在支持列表中
        is_deprecated = version not in SUPPORTED_VERSIONS
        
        return VersionInfo(
            version=version_str,
            is_deprecated=is_deprecated,
            successor_version=SUPPORTED_VERSIONS[-1].value if SUPPORTED_VERSIONS else None,
        )

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
        2. X-API-Version 请求头 (例如: X-API-Version: v2)
        3. Accept-Version 请求头 (例如: Accept-Version: v2)
        4. 默认版本

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

    # 版本协商请求头（按优先级排序）
    VERSION_HEADERS = ["X-API-Version", "Accept-Version"]

    def __init__(
        self,
        default_version: APIVersion = DEFAULT_VERSION,
        supported_versions: Optional[list[APIVersion]] = None,
        strict_mode: bool = False,
    ) -> None:
        """初始化版本协商器

        Args:
            default_version: 默认版本
            supported_versions: 支持的版本列表
            strict_mode: 严格模式，若为 True 则不支持的版本会抛出异常
        """
        self.default_version = default_version
        self.supported_versions = (
            supported_versions or SUPPORTED_VERSIONS.copy()
        )
        self.strict_mode = strict_mode

    def negotiate(self, request: Request) -> APIVersion:
        """协商确定API版本

        Args:
            request: FastAPI请求对象

        Returns:
            协商后的API版本

        Raises:
            ValueError: 在严格模式下请求了不支持的版本
        """
        path = request.url.path
        
        # 1. 优先从 URL 路径中提取版本
        path_version = self._extract_version_from_path(path)
        if path_version:
            return self._validate_version(path_version)

        # 2. 从请求头中提取版本（按优先级顺序）
        header_version = self._extract_version_from_headers(request)
        if header_version:
            return self._validate_version(header_version)

        return self.default_version

    def negotiate_with_info(self, request: Request) -> tuple[APIVersion, VersionInfo]:
        """协商版本并返回详细信息

        Args:
            request: FastAPI请求对象

        Returns:
            (版本, 版本信息) 元组
        """
        version = self.negotiate(request)
        version_info = self._get_version_info(version)
        return version, version_info

    def _validate_version(self, version: APIVersion) -> APIVersion:
        """验证版本是否支持

        Args:
            version: 待验证的版本

        Returns:
            验证通过的版本

        Raises:
            ValueError: 在严格模式下版本不支持
        """
        if version not in self.supported_versions:
            if self.strict_mode:
                raise ValueError(
                    f"不支持的 API 版本: {version.value}。"
                    f"支持的版本: {', '.join(v.value for v in self.supported_versions)}"
                )
            # 非严格模式下，返回默认版本
            logger.warning(
                f"请求了不支持的版本 {version.value}，回退到默认版本 {self.default_version.value}"
            )
            return self.default_version
        return version

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
                return APIVersion(version_str)
            except ValueError:
                pass
        return None

    def _extract_version_from_headers(
        self, request: Request
    ) -> Optional[APIVersion]:
        """从请求头中提取版本（支持多种请求头）

        优先级：X-API-Version > Accept-Version

        Args:
            request: FastAPI请求对象

        Returns:
            API版本，如果无法提取则返回None
        """
        for header_name in self.VERSION_HEADERS:
            header_value = request.headers.get(header_name, "").strip()
            if not header_value:
                continue

            # 标准化版本字符串
            if not header_value.startswith("v"):
                header_value = f"v{header_value}"

            try:
                return APIVersion(header_value.lower())
            except ValueError:
                logger.debug(
                    f"无效的版本头 {header_name}: {header_value}"
                )

        return None

    def _get_version_info(self, version: APIVersion) -> VersionInfo:
        """获取版本的详细信息

        Args:
            version: API版本

        Returns:
            VersionInfo 实例
        """
        version_str = version.value

        # 检查是否在废弃配置中
        if version_str in DEPRECATED_VERSIONS_CONFIG:
            config = DEPRECATED_VERSIONS_CONFIG[version_str]
            return VersionInfo(
                version=version_str,
                is_deprecated=True,
                sunset_date=config.get("sunset_date"),
                successor_version=config.get("successor_version"),
                deprecation_message=config.get("deprecation_message"),
            )

        # 检查是否在支持列表中
        is_deprecated = version not in self.supported_versions

        return VersionInfo(
            version=version_str,
            is_deprecated=is_deprecated,
            successor_version=self.supported_versions[-1].value if self.supported_versions else None,
        )

    def check_compatibility(
        self,
        requested_version: APIVersion,
        min_version: Optional[APIVersion] = None,
        max_version: Optional[APIVersion] = None,
    ) -> VersionCompatibilityResult:
        """检查版本兼容性

        Args:
            requested_version: 请求的版本
            min_version: 最低支持版本
            max_version: 最高支持版本

        Returns:
            VersionCompatibilityResult 兼容性检查结果
        """
        warnings = []
        is_compatible = True
        effective_version = requested_version

        # 检查版本是否支持
        if requested_version not in self.supported_versions:
            is_compatible = False
            warnings.append(
                f"版本 {requested_version.value} 不在支持列表中"
            )
            effective_version = self.default_version

        # 检查最低版本
        if min_version and requested_version < min_version:
            is_compatible = False
            warnings.append(
                f"请求的版本 {requested_version.value} 低于最低支持版本 {min_version.value}"
            )
            effective_version = min_version

        # 检查最高版本
        if max_version and requested_version > max_version:
            warnings.append(
                f"请求的版本 {requested_version.value} 高于最高测试版本 {max_version.value}，"
                f"可能存在兼容性问题"
            )

        # 检查是否已废弃
        version_info = self._get_version_info(requested_version)
        if version_info.is_deprecated:
            warnings.append(
                version_info.deprecation_message or
                f"版本 {requested_version.value} 已废弃"
            )
            if version_info.successor_version:
                warnings.append(
                    f"请迁移到版本 {version_info.successor_version}"
                )

        return VersionCompatibilityResult(
            is_compatible=is_compatible,
            requested_version=requested_version.value,
            effective_version=effective_version.value,
            warnings=warnings,
            migration_guide=None,  # 可扩展添加迁移指南 URL
        )

    def get_supported_versions(self) -> list[str]:
        """获取支持的版本列表

        Returns:
            支持的版本字符串列表
        """
        return [v.value for v in self.supported_versions]

    def get_latest_version(self) -> APIVersion:
        """获取最新版本

        Returns:
            最新支持的版本
        """
        return self.supported_versions[-1] if self.supported_versions else self.default_version


def get_current_api_version(request: Request) -> APIVersion:
    """获取当前请求的API版本

    Args:
        request: FastAPI请求对象

    Returns:
        当前API版本，如果未设置则返回默认版本
    """
    return getattr(request.state, "api_version", DEFAULT_VERSION)


def get_version_info(request: Request) -> VersionInfo:
    """获取当前请求的版本详细信息

    Args:
        request: FastAPI请求对象

    Returns:
        VersionInfo 实例，如果未设置则返回默认版本信息
    """
    return getattr(
        request.state,
        "api_version_info",
        VersionInfo(version=DEFAULT_VERSION.value)
    )


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
    include_deprecation_headers: bool = True,
) -> JSONResponse:
    """创建带版本信息的响应

    自动添加版本相关的响应头。

    Args:
        data: 响应数据
        request: FastAPI请求对象
        deprecated: 是否标记为弃用
        include_deprecation_headers: 是否包含废弃相关响应头

    Returns:
        JSONResponse响应对象

    响应头:
        - X-API-Version: 当前API版本
        - X-API-Deprecated: 是否已废弃
        - X-API-Sunset: 废弃日期
        - X-API-Latest-Version: 最新版本
        - X-API-Supported-Versions: 支持的版本列表
        - Link: 接替版本链接
        - Warning: 废弃警告
    """
    response = JSONResponse(content=data)

    version = get_current_api_version(request)
    response.headers["X-API-Version"] = version.value
    
    # 添加支持的版本列表
    response.headers["X-API-Supported-Versions"] = ", ".join(
        v.value for v in SUPPORTED_VERSIONS
    )

    # 添加废弃相关响应头
    if include_deprecation_headers and (deprecated or is_api_deprecated(request)):
        version_info = get_version_info(request)
        deprecation_headers = version_info.to_response_headers(request.url.path)
        for header_name, header_value in deprecation_headers.items():
            response.headers[header_name] = header_value

    return response


def create_deprecation_warning_response(
    data: Any,
    request: Request,
    sunset_date: Optional[str] = None,
    successor_version: Optional[str] = None,
    deprecation_message: Optional[str] = None,
) -> JSONResponse:
    """创建带废弃警告的响应

    用于主动标记即将废弃的端点。

    Args:
        data: 响应数据
        request: FastAPI请求对象
        sunset_date: 废弃日期（RFC 7231 格式）
        successor_version: 接替版本
        deprecation_message: 废弃提示信息

    Returns:
        JSONResponse响应对象
    """
    version = get_current_api_version(request)
    
    version_info = VersionInfo(
        version=version.value,
        is_deprecated=True,
        sunset_date=sunset_date,
        successor_version=successor_version or SUPPORTED_VERSIONS[-1].value,
        deprecation_message=deprecation_message,
    )
    
    response = JSONResponse(content=data)
    response.headers["X-API-Version"] = version.value
    response.headers["X-API-Deprecated"] = "true"
    
    if sunset_date:
        response.headers["X-API-Sunset"] = sunset_date
    
    if successor_version:
        response.headers["X-API-Latest-Version"] = successor_version
    
    if deprecation_message:
        response.headers["Warning"] = f'299 - "{deprecation_message}"'
    
    return response


def get_api_version_headers(request: Request) -> dict[str, str]:
    """获取API版本相关的响应头

    用于在非 JSONResponse 响应中添加版本头。

    Args:
        request: FastAPI请求对象

    Returns:
        响应头字典
    """
    version = get_current_api_version(request)
    headers = {
        "X-API-Version": version.value,
        "X-API-Supported-Versions": ", ".join(v.value for v in SUPPORTED_VERSIONS),
    }
    
    version_info = get_version_info(request)
    if version_info.is_deprecated:
        deprecation_headers = version_info.to_response_headers(request.url.path)
        headers.update(deprecation_headers)
    
    return headers


def check_version_compatibility(
    request: Request,
    min_version: Optional[APIVersion] = None,
    max_version: Optional[APIVersion] = None,
) -> VersionCompatibilityResult:
    """检查当前请求的版本兼容性

    用于在路由处理器中检查版本兼容性。

    Args:
        request: FastAPI请求对象
        min_version: 最低支持版本
        max_version: 最高支持版本

    Returns:
        VersionCompatibilityResult 兼容性检查结果

    Example:
        ```python
        from fastapi import Request
        from app.core.versioning import check_version_compatibility, APIVersion

        @router.get("/feature")
        async def new_feature(request: Request):
            # 检查版本兼容性
            result = check_version_compatibility(
                request,
                min_version=APIVersion.V2,
            )
            
            if not result.is_compatible:
                return {"error": "此功能需要 API v2 或更高版本", "warnings": result.warnings}
            
            # 功能逻辑...
        ```
    """
    current_version = get_current_api_version(request)
    return version_negotiator.check_compatibility(
        current_version,
        min_version=min_version,
        max_version=max_version,
    )


def require_min_version(min_version: APIVersion):
    """版本要求装饰器

    用于要求最低 API 版本的路由。

    Args:
        min_version: 最低要求的 API 版本

    Returns:
        装饰器函数

    Example:
        ```python
        from fastapi import Request, HTTPException
        from app.core.versioning import require_min_version, APIVersion

        @router.get("/new-feature")
        @require_min_version(APIVersion.V2)
        async def new_feature(request: Request):
            return {"feature": "only available in v2+"}
        ```

    Note:
        这是一个占位装饰器，实际使用时应在路由处理函数内部
        调用 check_version_compatibility 进行检查。
    """
    def decorator(func):
        async def wrapper(*args, request: Request = None, **kwargs):
            # 查找 request 参数
            req = request
            if req is None:
                for arg in args:
                    if isinstance(arg, Request):
                        req = arg
                        break
            
            if req:
                result = check_version_compatibility(req, min_version=min_version)
                if not result.is_compatible:
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": f"此功能需要 {min_version.value} 或更高版本",
                            "warnings": result.warnings,
                            "current_version": result.requested_version,
                            "required_version": min_version.value,
                        }
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ============================================================================
# 全局实例
# ============================================================================

versioned_router = VersionedRouter()
version_negotiator = VersionNegotiator()


# ============================================================================
# 配置函数
# ============================================================================

def setup_versioning(
    app: FastAPI,
    default_version: APIVersion = DEFAULT_VERSION,
    include_supported_versions_header: bool = True,
) -> None:
    """设置API版本控制

    为FastAPI应用配置版本控制中间件。

    Args:
        app: FastAPI应用实例
        default_version: 默认API版本
        include_supported_versions_header: 是否在响应中包含支持的版本列表

    Example:
        ```python
        from fastapi import FastAPI
        from app.core.versioning import setup_versioning

        app = FastAPI()
        setup_versioning(app)
        ```
    """
    app.add_middleware(
        APIVersionMiddleware,
        default_version=default_version,
        include_supported_versions_header=include_supported_versions_header,
    )


def configure_deprecated_version(
    version: str,
    sunset_date: str,
    successor_version: Optional[str] = None,
    deprecation_message: Optional[str] = None,
) -> None:
    """配置废弃版本

    运行时配置废弃版本的详细信息。

    Args:
        version: 要废弃的版本号（如 "v1"）
        sunset_date: 废弃日期（RFC 7231 格式，如 "2027-01-01T00:00:00Z"）
        successor_version: 接替版本（如 "v2"）
        deprecation_message: 废弃提示信息

    Example:
        ```python
        from app.core.versioning import configure_deprecated_version

        # 在应用启动时配置废弃版本
        configure_deprecated_version(
            version="v1",
            sunset_date="2027-01-01T00:00:00Z",
            successor_version="v2",
            deprecation_message="API v1 已废弃，请迁移到 v2",
        )
        ```
    """
    global DEPRECATED_VERSIONS_CONFIG
    
    DEPRECATED_VERSIONS_CONFIG[version] = {
        "sunset_date": sunset_date,
        "successor_version": successor_version,
        "deprecation_message": deprecation_message,
    }
    
    logger.info(
        f"已配置废弃版本: {version}, "
        f"废弃日期: {sunset_date}, "
        f"接替版本: {successor_version}"
    )


def get_version_config() -> dict[str, Any]:
    """获取版本配置信息

    用于管理端点展示当前版本配置。

    Returns:
        版本配置字典
    """
    return {
        "default_version": DEFAULT_VERSION.value,
        "supported_versions": [v.value for v in SUPPORTED_VERSIONS],
        "deprecated_versions": DEPRECATED_VERSIONS_CONFIG.copy(),
        "latest_version": SUPPORTED_VERSIONS[-1].value if SUPPORTED_VERSIONS else None,
    }
