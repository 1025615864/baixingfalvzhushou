"""API版本控制测试

测试版本控制模块的所有功能，包括：
- 版本枚举和配置
- 版本化路由器
- 版本协商（URL路径、X-API-Version、Accept-Version）
- 版本兼容性检查
- 废弃版本处理
- 版本化响应
"""
import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.core.versioning import (
    APIVersion,
    VersionInfo,
    VersionCompatibilityResult,
    VersionedRouter,
    VersionNegotiator,
    APIVersionMiddleware,
    get_current_api_version,
    get_version_info,
    is_api_deprecated,
    create_versioned_response,
    create_deprecation_warning_response,
    get_api_version_headers,
    check_version_compatibility,
    setup_versioning,
    configure_deprecated_version,
    get_version_config,
    DEFAULT_VERSION,
    SUPPORTED_VERSIONS,
    DEPRECATED_VERSIONS_CONFIG,
)


class TestAPIVersion:
    """API版本测试"""

    def test_version_enum_values(self):
        """测试版本枚举值"""
        assert APIVersion.V1.value == "v1"
        assert APIVersion.V2.value == "v2"
        assert APIVersion.V3.value == "v3"

    def test_supported_versions(self):
        """测试支持的版本"""
        assert APIVersion.V1 in SUPPORTED_VERSIONS
        assert APIVersion.V2 in SUPPORTED_VERSIONS
        assert APIVersion.V3 in SUPPORTED_VERSIONS


class TestVersionedRouter:
    """版本化路由器测试"""

    def test_create_router(self):
        """测试创建路由器"""
        router = VersionedRouter()
        assert router.prefix == "/api"

    def test_get_router(self):
        """测试获取指定版本路由器"""
        router = VersionedRouter()

        v1 = router.get_router(APIVersion.V1)
        assert v1 is not None
        assert v1.prefix == "/api/v1"

        v2 = router.get_router(APIVersion.V2)
        assert v2 is not None
        assert v2.prefix == "/api/v2"

    def test_property_access(self):
        """测试属性访问"""
        router = VersionedRouter()

        assert router.v1 is not None
        assert router.v2 is not None
        assert router.v3 is not None

    def test_include_router(self):
        """测试包含路由器"""
        router = VersionedRouter()
        test_router = APIRouter()

        router.include_router(test_router, versions=[APIVersion.V1, APIVersion.V2])

        assert len(router._versioned_routes) == 1
        assert APIVersion.V1 in router._versioned_routes[0].versions
        assert APIVersion.V2 in router._versioned_routes[0].versions

    def test_get_version_info(self):
        """测试获取版本信息"""
        router = VersionedRouter()
        test_router = APIRouter()
        router.include_router(test_router, versions=[APIVersion.V1])

        info = router.get_version_info()
        assert info["default_version"] == "v1"
        assert "v1" in info["supported_versions"]
        assert len(info["routes"]) == 1


class TestVersionNegotiator:
    """版本协商器测试"""

    def test_default_version(self):
        """测试默认版本"""
        negotiator = VersionNegotiator()
        assert negotiator.default_version == DEFAULT_VERSION

    def test_supported_versions(self):
        """测试支持的版本"""
        negotiator = VersionNegotiator()
        assert APIVersion.V1 in negotiator.supported_versions
        assert APIVersion.V2 in negotiator.supported_versions

    def test_negotiate_with_supported_version(self):
        """测试协商支持的版本"""
        negotiator = VersionNegotiator()
        mock_request = MagicMock()
        mock_request.url.path = "/api/v2/users"
        mock_request.headers = {}

        version = negotiator.negotiate(mock_request)
        assert version == APIVersion.V2

    def test_negotiate_default(self):
        """测试默认协商"""
        negotiator = VersionNegotiator()
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.headers = {}

        version = negotiator.negotiate(mock_request)
        assert version == DEFAULT_VERSION


class TestHelperFunctions:
    """辅助函数测试"""

    def test_get_current_api_version(self):
        """测试获取当前API版本"""
        mock_request = MagicMock()
        mock_request.state.api_version = APIVersion.V2

        version = get_current_api_version(mock_request)
        assert version == APIVersion.V2

    def test_get_current_api_version_default(self):
        """测试获取默认API版本"""
        mock_request = MagicMock(spec=["state"])
        del mock_request.state.api_version

        version = get_current_api_version(mock_request)
        assert version == DEFAULT_VERSION

    def test_is_api_deprecated(self):
        """测试API弃用检查"""
        mock_request = MagicMock()
        mock_request.state.api_version_deprecated = True

        deprecated = is_api_deprecated(mock_request)
        assert deprecated is True


class TestVersionedResponse:
    """版本化响应测试"""

    def test_create_versioned_response(self):
        """测试创建版本化响应"""
        mock_request = MagicMock()
        mock_request.state.api_version = APIVersion.V1
        mock_request.state.api_version_deprecated = False

        response = create_versioned_response({"key": "value"}, mock_request)

        assert response.status_code == 200
        assert response.headers["X-API-Version"] == "v1"

    def test_create_deprecated_response(self):
        """测试创建弃用版本响应"""
        mock_request = MagicMock()
        mock_request.state.api_version = APIVersion.V3
        mock_request.state.api_version_deprecated = True

        response = create_versioned_response({"key": "value"}, mock_request, deprecated=True)

        assert response.headers["X-API-Version"] == "v3"
        assert response.headers["X-API-Deprecated"] == "true"


class TestVersionedRouterRoutes:
    """版本化路由测试"""

    def test_router_routes_are_separate(self):
        """测试不同版本的路由是独立的"""
        router = VersionedRouter()

        @router.v1.get("/test")
        async def v1_test():
            return {"version": "v1"}

        @router.v2.get("/test")
        async def v2_test():
            return {"version": "v2"}

        assert router.v1.routes[0].path == "/api/v1/test"
        assert router.v2.routes[0].path == "/api/v2/test"

    def test_router_tags(self):
        """测试路由标签"""
        router = VersionedRouter()

        assert "API v1" in router.v1.tags
        assert "API v2" in router.v2.tags
        assert "API v3" in router.v3.tags


class TestVersionNegotiationHeader:
    """版本协商请求头测试"""

    def test_header_based_negotiation(self):
        """测试基于请求头的版本协商"""
        negotiator = VersionNegotiator()
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.headers = {"Accept-Version": "v2"}

        version = negotiator.negotiate(mock_request)
        assert version == APIVersion.V2

    def test_path_priority_over_header(self):
        """测试路径优先于请求头（当前实现）"""
        negotiator = VersionNegotiator()
        mock_request = MagicMock()
        mock_request.url.path = "/api/v1/users"
        mock_request.headers = {"Accept-Version": "v2"}

        version = negotiator.negotiate(mock_request)
        assert version == APIVersion.V1


class TestXAPIVersionHeader:
    """X-API-Version 请求头测试"""

    def test_x_api_version_header_negotiation(self):
        """测试 X-API-Version 请求头版本协商"""
        negotiator = VersionNegotiator()
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.headers = {"X-API-Version": "v3"}

        version = negotiator.negotiate(mock_request)
        assert version == APIVersion.V3

    def test_x_api_version_priority_over_accept_version(self):
        """测试 X-API-Version 优先于 Accept-Version"""
        negotiator = VersionNegotiator()
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.headers = {
            "X-API-Version": "v3",
            "Accept-Version": "v2"
        }

        version = negotiator.negotiate(mock_request)
        assert version == APIVersion.V3

    def test_numeric_version_header(self):
        """测试数字格式的版本头"""
        negotiator = VersionNegotiator()
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.headers = {"X-API-Version": "2"}

        version = negotiator.negotiate(mock_request)
        assert version == APIVersion.V2


class TestVersionCompatibility:
    """版本兼容性检查测试"""

    def test_compatible_version(self):
        """测试兼容版本"""
        negotiator = VersionNegotiator()
        result = negotiator.check_compatibility(APIVersion.V2)

        assert result.is_compatible is True
        assert result.requested_version == "v2"
        assert result.effective_version == "v2"
        assert len(result.warnings) == 0

    def test_min_version_check(self):
        """测试最低版本检查"""
        negotiator = VersionNegotiator()
        result = negotiator.check_compatibility(
            APIVersion.V1,
            min_version=APIVersion.V2
        )

        assert result.is_compatible is False
        assert "低于最低支持版本" in result.warnings[0]

    def test_max_version_warning(self):
        """测试最高版本警告"""
        negotiator = VersionNegotiator()
        result = negotiator.check_compatibility(
            APIVersion.V3,
            max_version=APIVersion.V2
        )

        # 版本高于最高测试版本应该有警告
        assert len(result.warnings) > 0
        assert "高于最高测试版本" in result.warnings[0]

    def test_negotiate_with_info(self):
        """测试带详细信息的版本协商"""
        negotiator = VersionNegotiator()
        mock_request = MagicMock()
        mock_request.url.path = "/api/v2/users"
        mock_request.headers = {}

        version, info = negotiator.negotiate_with_info(mock_request)

        assert version == APIVersion.V2
        assert info.version == "v2"

    def test_get_supported_versions(self):
        """测试获取支持的版本列表"""
        negotiator = VersionNegotiator()
        versions = negotiator.get_supported_versions()

        assert "v1" in versions
        assert "v2" in versions
        assert "v3" in versions

    def test_get_latest_version(self):
        """测试获取最新版本"""
        negotiator = VersionNegotiator()
        latest = negotiator.get_latest_version()

        assert latest == APIVersion.V3


class TestVersionInfo:
    """VersionInfo 类测试"""

    def test_non_deprecated_version_headers(self):
        """测试非废弃版本的响应头"""
        info = VersionInfo(version="v2", is_deprecated=False)
        headers = info.to_response_headers("/api/v2/users")

        assert "X-API-Deprecated" not in headers
        assert "X-API-Sunset" not in headers

    def test_deprecated_version_headers(self):
        """测试废弃版本的响应头"""
        info = VersionInfo(
            version="v1",
            is_deprecated=True,
            sunset_date="Sat, 01 Jan 2027 00:00:00 GMT",
            successor_version="v2",
            deprecation_message="API v1 已废弃"
        )
        headers = info.to_response_headers("/api/v1/users")

        assert headers["X-API-Deprecated"] == "true"
        assert headers["X-API-Sunset"] == "Sat, 01 Jan 2027 00:00:00 GMT"
        assert headers["X-API-Latest-Version"] == "v2"
        assert "successor-version" in headers["Link"]
        assert "API v1 已废弃" in headers["Warning"]

    def test_link_header_generation(self):
        """测试 Link 头生成"""
        info = VersionInfo(
            version="v1",
            is_deprecated=True,
            successor_version="v2"
        )
        headers = info.to_response_headers("/api/v1/users/profile")

        assert "</api/v2/users/profile>" in headers["Link"]
        assert 'rel="successor-version"' in headers["Link"]


class TestDeprecationConfiguration:
    """废弃版本配置测试"""

    def test_configure_deprecated_version(self):
        """测试配置废弃版本"""
        # 保存原始配置
        original_config = DEPRECATED_VERSIONS_CONFIG.copy()
        
        try:
            configure_deprecated_version(
                version="v1",
                sunset_date="2027-01-01T00:00:00Z",
                successor_version="v2",
                deprecation_message="API v1 已废弃"
            )

            assert "v1" in DEPRECATED_VERSIONS_CONFIG
            assert DEPRECATED_VERSIONS_CONFIG["v1"]["sunset_date"] == "2027-01-01T00:00:00Z"
            assert DEPRECATED_VERSIONS_CONFIG["v1"]["successor_version"] == "v2"
        finally:
            # 恢复原始配置
            DEPRECATED_VERSIONS_CONFIG.clear()
            DEPRECATED_VERSIONS_CONFIG.update(original_config)

    def test_get_version_config(self):
        """测试获取版本配置"""
        config = get_version_config()

        assert "default_version" in config
        assert "supported_versions" in config
        assert "deprecated_versions" in config
        assert "latest_version" in config
        assert config["default_version"] == "v1"
        assert config["latest_version"] == "v3"


class TestStrictMode:
    """严格模式测试"""

    def test_strict_mode_rejects_unsupported_version(self):
        """测试严格模式拒绝不支持的版本"""
        negotiator = VersionNegotiator(strict_mode=True)
        mock_request = MagicMock()
        mock_request.url.path = "/api/v99/users"
        mock_request.headers = {}

        with pytest.raises(ValueError) as exc_info:
            negotiator.negotiate(mock_request)

        assert "不支持的 API 版本" in str(exc_info.value)

    def test_non_strict_mode_falls_back(self):
        """测试非严格模式回退到默认版本"""
        negotiator = VersionNegotiator(strict_mode=False)
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.headers = {"X-API-Version": "99"}

        version = negotiator.negotiate(mock_request)
        assert version == DEFAULT_VERSION


class TestHelperFunctionsExtended:
    """扩展的辅助函数测试"""

    def test_get_version_info(self):
        """测试获取版本详细信息"""
        mock_request = MagicMock()
        mock_request.state.api_version = APIVersion.V2
        mock_request.state.api_version_deprecated = False
        mock_request.state.api_version_info = VersionInfo(version="v2")

        info = get_version_info(mock_request)
        assert info.version == "v2"

    def test_get_api_version_headers(self):
        """测试获取 API 版本响应头"""
        mock_request = MagicMock()
        mock_request.state.api_version = APIVersion.V2
        mock_request.state.api_version_deprecated = False
        mock_request.state.api_version_info = VersionInfo(version="v2")
        mock_request.url.path = "/api/v2/users"

        headers = get_api_version_headers(mock_request)

        assert headers["X-API-Version"] == "v2"
        assert "v1" in headers["X-API-Supported-Versions"]

    def test_create_deprecation_warning_response(self):
        """测试创建废弃警告响应"""
        mock_request = MagicMock()
        mock_request.state.api_version = APIVersion.V1
        mock_request.url.path = "/api/v1/users"

        response = create_deprecation_warning_response(
            data={"key": "value"},
            request=mock_request,
            sunset_date="Sat, 01 Jan 2027 00:00:00 GMT",
            successor_version="v2",
            deprecation_message="API v1 已废弃"
        )

        assert response.headers["X-API-Deprecated"] == "true"
        assert response.headers["X-API-Sunset"] == "Sat, 01 Jan 2027 00:00:00 GMT"
        assert response.headers["X-API-Latest-Version"] == "v2"

    def test_check_version_compatibility_function(self):
        """测试版本兼容性检查函数"""
        mock_request = MagicMock()
        mock_request.state.api_version = APIVersion.V2
        mock_request.state.api_version_deprecated = False
        mock_request.state.api_version_info = VersionInfo(version="v2")

        result = check_version_compatibility(
            mock_request,
            min_version=APIVersion.V1,
            max_version=APIVersion.V3
        )

        assert result.is_compatible is True


class TestVersionedResponseExtended:
    """扩展的版本化响应测试"""

    def test_create_versioned_response_with_supported_versions(self):
        """测试版本化响应包含支持的版本列表"""
        mock_request = MagicMock()
        mock_request.state.api_version = APIVersion.V1
        mock_request.state.api_version_deprecated = False
        mock_request.state.api_version_info = VersionInfo(version="v1")
        mock_request.url.path = "/api/v1/users"

        response = create_versioned_response(
            {"key": "value"},
            mock_request,
            include_deprecation_headers=True
        )

        assert "X-API-Supported-Versions" in response.headers

    def test_create_versioned_response_without_deprecation_headers(self):
        """测试版本化响应不包含废弃头"""
        mock_request = MagicMock()
        mock_request.state.api_version = APIVersion.V1
        mock_request.state.api_version_deprecated = False
        mock_request.state.api_version_info = VersionInfo(version="v1")
        mock_request.url.path = "/api/v1/users"

        response = create_versioned_response(
            {"key": "value"},
            mock_request,
            include_deprecation_headers=False
        )

        assert "X-API-Deprecated" not in response.headers
