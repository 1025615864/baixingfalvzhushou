"""API 错误处理模块单元测试"""
import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from services.common.api.error_handler import (
    ErrorCode,
    ErrorResponse,
    create_error_response,
    create_http_exception,
    global_exception_handler,
)


class TestErrorCode:
    """ErrorCode 枚举测试"""

    def test_error_code_values(self):
        """测试错误码值"""
        assert ErrorCode.INTERNAL_ERROR.value == "SYS-001"
        assert ErrorCode.INVALID_REQUEST.value == "SYS-002"
        assert ErrorCode.NOT_FOUND.value == "SYS-003"
        assert ErrorCode.UNAUTHORIZED.value == "SYS-004"
        assert ErrorCode.FORBIDDEN.value == "SYS-005"
        assert ErrorCode.RATE_LIMITED.value == "SYS-006"
        assert ErrorCode.SERVICE_UNAVAILABLE.value == "SYS-007"
        assert ErrorCode.TIMEOUT.value == "SYS-008"

    def test_auth_error_codes(self):
        """测试认证错误码"""
        assert ErrorCode.AUTH_INVALID_TOKEN.value == "AUTH-001"
        assert ErrorCode.AUTH_TOKEN_EXPIRED.value == "AUTH-002"
        assert ErrorCode.AUTH_INVALID_CREDENTIALS.value == "AUTH-003"
        assert ErrorCode.AUTH_ACCOUNT_LOCKED.value == "AUTH-004"
        assert ErrorCode.AUTH_PASSWORD_EXPIRED.value == "AUTH-005"

    def test_all_codes_have_unique_values(self):
        """测试所有错误码值唯一"""
        values = [code.value for code in ErrorCode]
        assert len(values) == len(set(values))


class TestCreateErrorResponse:
    """create_error_response 函数测试"""

    def test_basic_error_response(self):
        """测试基础错误响应"""
        response = create_error_response(
            code=ErrorCode.NOT_FOUND.value,
            message="资源不存在",
            status_code=404,
        )

        assert response.status_code == 404
        body = json.loads(response.body.decode())
        assert body["code"] == "SYS-003"
        assert body["message"] == "资源不存在"
        assert "timestamp" in body

    def test_error_response_with_details(self):
        """测试带详情的错误响应"""
        response = create_error_response(
            code=ErrorCode.INVALID_REQUEST.value,
            message="参数错误",
            details={"field": "email", "error": "invalid format"},
            request_id="req-123",
        )

        body = json.loads(response.body.decode())
        assert body["details"]["field"] == "email"
        assert body["request_id"] == "req-123"

    def test_error_response_status_code(self):
        """测试不同状态码的响应"""
        for status_code in [400, 401, 403, 404, 429, 500, 503]:
            response = create_error_response(
                code=ErrorCode.INTERNAL_ERROR.value,
                message="Error",
                status_code=status_code,
            )
            assert response.status_code == status_code

    def test_error_response_content_type(self):
        """测试响应内容类型"""
        response = create_error_response(
            code=ErrorCode.INTERNAL_ERROR.value,
            message="Error",
        )

        assert response.headers["content-type"] == "application/json"


class TestCreateHttpException:
    """create_http_exception 函数测试"""

    def test_basic_http_exception(self):
        """测试基础 HTTP 异常"""
        exc = create_http_exception(
            code=ErrorCode.UNAUTHORIZED.value,
            message="未授权",
            status_code=401,
        )

        assert exc.status_code == 401
        assert isinstance(exc.detail, dict)
        assert exc.detail["code"] == "SYS-004"
        assert exc.detail["message"] == "未授权"

    def test_http_exception_with_details(self):
        """测试带详情的 HTTP 异常"""
        exc = create_http_exception(
            code=ErrorCode.INVALID_REQUEST.value,
            message="参数错误",
            details={"field": "name", "value": ""},
        )

        assert exc.detail["details"]["field"] == "name"

    def test_http_exception_with_request_id(self):
        """测试带 request_id 的 HTTP 异常"""
        exc = create_http_exception(
            code=ErrorCode.INTERNAL_ERROR.value,
            message="Error",
            request_id="req-456",
        )

        assert exc.detail["request_id"] == "req-456"

    def test_http_exception_default_status_code(self):
        """测试默认状态码"""
        exc = create_http_exception(
            code=ErrorCode.INTERNAL_ERROR.value,
            message="Error",
        )

        assert exc.status_code == 500


class TestGlobalExceptionHandler:
    """global_exception_handler 函数测试"""

    @pytest.mark.asyncio
    async def test_handle_http_exception_with_dict_detail(self):
        """测试处理 HTTP 异常（字典 detail）"""
        mock_request = MagicMock()
        mock_request.headers = {"x-request-id": "req-789"}

        exc = HTTPException(
            status_code=400,
            detail={
                "code": ErrorCode.INVALID_REQUEST.value,
                "message": "请求参数错误",
            },
        )

        response = await global_exception_handler(mock_request, exc)

        assert response.status_code == 400
        body = json.loads(response.body.decode())
        assert body["code"] == "SYS-002"
        assert body["message"] == "请求参数错误"
        assert body["request_id"] == "req-789"

    @pytest.mark.asyncio
    async def test_handle_http_exception_with_string_detail(self):
        """测试处理 HTTP 异常（字符串 detail）"""
        mock_request = MagicMock()
        mock_request.headers = {"x-request-id": "req-abc"}

        exc = HTTPException(status_code=404, detail="Not found")

        response = await global_exception_handler(mock_request, exc)

        assert response.status_code == 404
        body = json.loads(response.body.decode())
        assert body["code"] == "SYS-001"
        assert body["message"] == "内部服务器错误"

    @pytest.mark.asyncio
    async def test_handle_generic_exception(self):
        """测试处理通用异常"""
        mock_request = MagicMock()
        mock_request.headers = {"x-request-id": "req-def"}

        exc = ValueError("Something went wrong")

        response = await global_exception_handler(mock_request, exc)

        assert response.status_code == 500
        body = json.loads(response.body.decode())
        assert body["code"] == "SYS-001"

    @pytest.mark.asyncio
    async def test_handle_exception_without_request_id(self):
        """测试无 request_id 时的处理"""
        mock_request = MagicMock()
        mock_request.headers = {}

        exc = ValueError("Error")

        response = await global_exception_handler(mock_request, exc)

        body = json.loads(response.body.decode())
        assert body["request_id"] is None

    @pytest.mark.asyncio
    async def test_handle_runtime_error(self):
        """测试处理 RuntimeError"""
        mock_request = MagicMock()
        mock_request.headers = {}

        exc = RuntimeError("Runtime error")

        response = await global_exception_handler(mock_request, exc)

        assert response.status_code == 500


class TestErrorResponse:
    """ErrorResponse 数据类测试"""

    def test_error_response_structure(self):
        """测试错误响应结构"""
        response = ErrorResponse(
            code=ErrorCode.NOT_FOUND.value,
            message="Not found",
            status_code=404,
            timestamp="2024-01-01T00:00:00",
        )

        assert response.code == "SYS-003"
        assert response.message == "Not found"
        assert response.status_code == 404

    def test_error_response_with_optional_fields(self):
        """测试可选字段"""
        response = ErrorResponse(
            code=ErrorCode.INVALID_REQUEST.value,
            message="Invalid",
            status_code=400,
            details={"field": "email"},
            request_id="req-123",
            timestamp="2024-01-01T00:00:00",
        )

        assert response.details["field"] == "email"
        assert response.request_id == "req-123"
