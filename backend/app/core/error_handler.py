"""全局异常处理模块

提供FastAPI应用的全局异常捕获和统一错误响应格式化功能。
支持多种异常类型的统一处理，包括业务异常、HTTP异常、验证异常等。

功能特性:
    - 全局异常捕获和统一响应格式
    - 支持调试模式的详细错误信息
    - 自动记录异常日志
    - 支持请求ID追踪
    - 支持多种异常类型的差异化处理
    - 支持新旧两种响应格式 (success/message/data/error_code 和 ok/error)

错误响应格式 (新格式):
    ```json
    {
        "success": false,
        "message": "资源不存在",
        "data": null,
        "error_code": 1004
    }
    ```

使用示例:
    ```python
    from fastapi import FastAPI
    from app.core.error_handler import setup_exception_handling

    app = FastAPI()

    # 初始化异常处理
    handler = setup_exception_handling(app, debug=True)

    # 现在所有异常都会被统一处理
    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        if user_id <= 0:
            from app.core import ValidationException
            raise ValidationException("用户ID必须大于0")
        return {"user_id": user_id}
    ```
"""
from __future__ import annotations

import logging
import time
import traceback
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import BusinessException
from .response import ErrorCode, error_response

logger = logging.getLogger("api.error")

# HTTP状态码到业务错误码的映射
HTTP_STATUS_TO_ERROR_CODE = {
    400: ErrorCode.INVALID_PARAMS,
    401: ErrorCode.UNAUTHORIZED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    409: ErrorCode.CONFLICT,
    413: ErrorCode.AI_REQUEST_TOO_LONG,
    422: ErrorCode.VALIDATION_ERROR,
    429: ErrorCode.RATE_LIMIT_EXCEEDED,
    502: ErrorCode.AI_RESPONSE_INVALID,
    503: ErrorCode.AI_SERVICE_UNAVAILABLE,
    504: ErrorCode.AI_TIMEOUT,
}


def _get_error_code_from_status(status_code: int) -> ErrorCode:
    """根据HTTP状态码获取对应的业务错误码

    Args:
        status_code: HTTP状态码

    Returns:
        对应的业务错误码
    """
    return HTTP_STATUS_TO_ERROR_CODE.get(status_code, ErrorCode.INTERNAL_ERROR)


class ErrorResponseBuilder:
    """错误响应构建器

    用于构建标准化的错误响应对象。支持两种格式：
    1. 新格式 (success/message/data/error_code)
    2. 旧格式 (ok/error) - 保持向后兼容
    """

    @staticmethod
    def build_new_format(
        message: str,
        error_code: ErrorCode,
        request_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """构建新格式错误响应

        Args:
            message: 错误描述信息
            error_code: 业务错误码
            request_id: 请求ID，用于追踪
            details: 额外详细信息

        Returns:
            新格式的错误响应字典 (success/message/data/error_code)
        """
        result = error_response(
            message=message,
            error_code=error_code.value,
            data=details,
        )
        if request_id:
            result["request_id"] = request_id
        return result

    @staticmethod
    def build_old_format(
        message: str,
        code: str,
        status_code: int,
        request_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        include_traceback: bool = False,
    ) -> dict[str, Any]:
        """构建旧格式错误响应 (向后兼容)

        Args:
            message: 错误描述信息
            code: 错误码标识
            status_code: HTTP状态码
            request_id: 请求ID，用于追踪
            details: 额外详细信息
            include_traceback: 是否包含堆栈跟踪（仅调试模式使用）

        Returns:
            旧格式的错误响应字典 (ok/error)
        """
        response: dict[str, Any] = {
            "ok": False,
            "error": {
                "message": message,
                "code": code,
                "status": status_code,
                "ts": int(time.time()),
            }
        }

        if request_id:
            response["error"]["request_id"] = request_id

        if details:
            response["error"]["details"] = details

        if include_traceback:
            response["error"]["traceback"] = traceback.format_exc()

        return response


class GlobalExceptionHandler:
    """全局异常处理器

    FastAPI应用的全局异常处理中心，负责捕获和处理所有类型的异常。
    支持新格式 (success/message/data/error_code) 响应。

    支持的异常类型:
        1. BaseException - 所有自定义异常的基类
        2. BusinessException - 业务逻辑异常
        3. StarletteHTTPException - HTTP异常
        4. RequestValidationError - 请求参数验证异常
        5. Exception - 未处理的未知异常
    """

    def __init__(self, app: FastAPI, debug: bool = False) -> None:
        self.app = app
        self.debug = debug
        self._register_handlers()

    def _register_handlers(self) -> None:
        """注册所有异常处理器"""
        self.app.add_exception_handler(
            BusinessException, self._handle_business_exception
        )
        self.app.add_exception_handler(
            StarletteHTTPException, self._handle_http_exception
        )
        self.app.add_exception_handler(
            RequestValidationError, self._handle_validation_error
        )
        self.app.add_exception_handler(
            Exception, self._handle_unhandled_exception
        )

    def _get_request_id(self, request: Request) -> Optional[str]:
        """从请求状态中获取请求ID"""
        return str(getattr(request.state, "request_id", "") or "").strip() or None

    async def _handle_business_exception(
        self, request: Request, exc: BusinessException
    ) -> JSONResponse:
        """处理业务异常

        Args:
            request: FastAPI请求对象
            exc: 业务异常实例

        Returns:
            JSON响应
        """
        request_id = self._get_request_id(request)

        logger.warning(
            f"Business exception: {exc.message} (code: {exc.code}, "
            f"status: {exc.status_code}) - path: {request.url.path}"
        )

        # 尝试从异常中获取ErrorCode
        error_code_value = getattr(exc, "error_code", None)
        if error_code_value is not None and isinstance(error_code_value, ErrorCode):
            error_code = error_code_value
        else:
            # 尝试从code字符串映射到ErrorCode
            try:
                error_code = ErrorCode[exc.code]
            except KeyError:
                error_code = _get_error_code_from_status(exc.status_code)

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponseBuilder.build_new_format(
                message=exc.message,
                error_code=error_code,
                request_id=request_id,
                details=exc.details if self.debug else None,
            ),
            headers=getattr(exc, "headers", None),
        )

    async def _handle_http_exception(
        self, request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """处理HTTP异常

        Args:
            request: FastAPI请求对象
            exc: HTTP异常实例

        Returns:
            JSON响应
        """
        request_id = self._get_request_id(request)

        detail = exc.detail
        if isinstance(detail, dict):
            message = detail.get("message", str(exc.detail))
            # 如果detail中包含ErrorCode，使用它
            error_code_value = detail.get("error_code")
            if error_code_value is not None:
                try:
                    error_code = ErrorCode(error_code_value)
                except (ValueError, TypeError):
                    error_code = _get_error_code_from_status(exc.status_code)
            else:
                error_code = _get_error_code_from_status(exc.status_code)

            return JSONResponse(
                status_code=exc.status_code,
                content=ErrorResponseBuilder.build_new_format(
                    message=message,
                    error_code=error_code,
                    request_id=request_id,
                    details=detail.get("details") if self.debug else None,
                ),
                headers=exc.headers,
            )

        logger.warning(
            f"HTTP exception: {exc.status_code} - {str(exc.detail)} "
            f"- path: {request.url.path}"
        )

        message = str(exc.detail)
        error_code = _get_error_code_from_status(exc.status_code)

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponseBuilder.build_new_format(
                message=message,
                error_code=error_code,
                request_id=request_id,
            ),
            headers=exc.headers,
        )

    async def _handle_validation_error(
        self, request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """处理请求验证异常

        Args:
            request: FastAPI请求对象
            exc: 验证异常实例

        Returns:
            JSON响应（状态码422）
        """
        request_id = self._get_request_id(request)

        errors: list[dict[str, Any]] = []
        for error in exc.errors():
            loc = error.get("loc", [])
            msg = error.get("msg", "")
            typ = error.get("type", "")

            errors.append({
                "field": ".".join(str(l) for l in loc) if loc else "unknown",
                "message": msg,
                "type": typ,
            })

        logger.warning(
            f"Validation error: {len(errors)} errors - path: {request.url.path}"
        )

        details = {"errors": errors} if self.debug else None

        return JSONResponse(
            status_code=422,
            content=ErrorResponseBuilder.build_new_format(
                message="请求参数验证失败",
                error_code=ErrorCode.VALIDATION_ERROR,
                request_id=request_id,
                details=details,
            ),
        )

    async def _handle_unhandled_exception(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """处理未捕获的异常

        Args:
            request: FastAPI请求对象
            exc: 异常实例

        Returns:
            JSON响应（状态码500）
        """
        request_id = self._get_request_id(request)

        logger.exception(
            f"Unhandled exception: {type(exc).__name__} - {str(exc)} "
            f"- path: {request.url.path}"
        )

        message = "服务器内部错误" if not self.debug else str(exc)
        details = {"exception_type": type(exc).__name__} if self.debug else None

        return JSONResponse(
            status_code=500,
            content=ErrorResponseBuilder.build_new_format(
                message=message,
                error_code=ErrorCode.INTERNAL_ERROR,
                request_id=request_id,
                details=details,
            ),
        )


def setup_exception_handling(
    app: FastAPI, debug: bool = False
) -> GlobalExceptionHandler:
    """设置全局异常处理

    为FastAPI应用配置全局异常处理器。

    Args:
        app: FastAPI应用实例
        debug: 是否启用调试模式。调试模式下会返回详细错误信息

    Returns:
        GlobalExceptionHandler实例，可用于后续配置

    Examples:
        ```python
        from fastapi import FastAPI
        from app.core.error_handler import setup_exception_handling

        app = FastAPI()

        # 基础使用
        handler = setup_exception_handling(app)

        # 调试模式
        handler = setup_exception_handling(app, debug=True)
        ```
    """
    return GlobalExceptionHandler(app, debug)


# ============================================================
# 独立的异常处理器函数 (用于直接注册)
# ============================================================


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常统一处理函数

    Args:
        request: FastAPI请求对象
        exc: HTTP异常实例

    Returns:
        JSON响应
    """
    request_id = str(getattr(request.state, "request_id", "") or "").strip() or None
    error_code = _get_error_code_from_status(exc.status_code)

    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message", str(exc.detail))
    else:
        message = str(detail)

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponseBuilder.build_new_format(
            message=message,
            error_code=error_code,
            request_id=request_id,
        ),
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求体验证错误处理函数

    Args:
        request: FastAPI请求对象
        exc: 验证异常实例

    Returns:
        JSON响应（状态码422）
    """
    request_id = str(getattr(request.state, "request_id", "") or "").strip() or None

    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        loc = error.get("loc", [])
        msg = error.get("msg", "")
        typ = error.get("type", "")

        errors.append({
            "field": ".".join(str(l) for l in loc) if loc else "unknown",
            "message": msg,
            "type": typ,
        })

    return JSONResponse(
        status_code=422,
        content=ErrorResponseBuilder.build_new_format(
            message="请求参数验证失败",
            error_code=ErrorCode.VALIDATION_ERROR,
            request_id=request_id,
            details={"errors": errors},
        ),
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理函数

    Args:
        request: FastAPI请求对象
        exc: 异常实例

    Returns:
        JSON响应（状态码500）
    """
    request_id = str(getattr(request.state, "request_id", "") or "").strip() or None

    logger.exception(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)} "
        f"- path: {request.url.path}"
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponseBuilder.build_new_format(
            message="服务器内部错误",
            error_code=ErrorCode.INTERNAL_ERROR,
            request_id=request_id,
            details={"exception_type": type(exc).__name__},
        ),
    )