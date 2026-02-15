"""API版本控制测试"""
import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.core.versioning import (
    APIVersion,
    VersionedRouter,
    VersionNegotiator,
    get_current_api_version,
    is_api_deprecated,
    create_versioned_response,
    DEFAULT_VERSION,
    SUPPORTED_VERSIONS,
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
