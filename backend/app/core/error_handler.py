"""全局异常处理模块

提供FastAPI应用的全局异常捕获和统一错误响应格式化功能。
支持多种异常类型的统一处理，包括业务异常、HTTP异常、验证异常等。

功能特性:
    - 全局异常捕获和统一响应格式
    - 支持调试模式的详细错误信息
    - 自动记录异常日志
    - 支持请求ID追踪
    - 支持多种异常类型的差异化处理

错误响应格式:
    ```json
    {
        "ok": false,
        "error": {
            "message": "资源不存在",
            "code": "NOT_FOUND",
            "status": 404,
            "ts": 1699999999,
            "request_id": "req_abc123",
            "details": {...},
            "traceback": "..."
        }
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

logger = logging.getLogger("api.error")


class ErrorResponseBuilder:
    """错误响应构建器

    用于构建标准化的错误响应对象。

    响应结构:
        - ok: 始终为false
        - error: 错误详情对象
            - message: 错误信息
            - code: 错误码
            - status: HTTP状态码
            - ts: 时间戳
            - request_id: 请求ID（可选）
            - details: 详细信息（可选）
            - traceback: 堆栈跟踪（调试模式可选）

    Examples:
        ```python
        response = ErrorResponseBuilder.build(
            message="资源不存在",
            code="NOT_FOUND",
            status_code=404,
            request_id="req_123",
            details={"user_id": 123}
        )
        # 输出:
        # {
        #     "ok": False,
        #     "error": {
        #         "message": "资源不存在",
        #         "code": "NOT_FOUND",
        #         "status": 404,
        #         "ts": 1699999999,
        #         "request_id": "req_123",
        #         "details": {"user_id": 123}
        #     }
        # }
        ```
    """

    @staticmethod
    def build(
        message: str,
        code: str,
        status_code: int,
        request_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        include_traceback: bool = False,
    ) -> dict[str, Any]:
        """构建标准错误响应

        Args:
            message: 错误描述信息
            code: 错误码标识
            status_code: HTTP状态码
            request_id: 请求ID，用于追踪
            details: 额外详细信息
            include_traceback: 是否包含堆栈跟踪（仅调试模式使用）

        Returns:
            标准化的错误响应字典
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

    支持的异常类型:
        1. BaseException - 所有自定义异常的基类
        2. BusinessException - 业务逻辑异常
        3. StarletteHTTPException - HTTP异常
        4. RequestValidationError - 请求参数验证异常
        5. Exception - 未处理的未知异常

    处理策略:
        - 业务异常: 记录警告日志，返回对应HTTP状态码
        - HTTP异常: 直接透传状态码和消息
        - 验证异常: 提取详细错误信息，返回422
        - 未处理异常: 记录错误日志，返回500

    Attributes:
        app: FastAPI应用实例
        debug: 是否调试模式（显示详细信息）
    """

    def __init__(self, app: FastAPI, debug: bool = False) -> None:
        self.app = app
        self.debug = debug
        self._register_handlers()

    def _register_handlers(self) -> None:
        """注册所有异常处理器

        为FastAPI应用注册各类异常的处理函数。
        处理器按照从具体到一般的顺序注册。
        """
        # 使用自定义异常类作为基类
        # type: ignore[arg-type] - FastAPI类型系统的已知限制，运行时正常工作
        self.app.add_exception_handler(
            BusinessException, self._handle_business_exception  # type: ignore[arg-type]
        )
        self.app.add_exception_handler(
            StarletteHTTPException, self._handle_http_exception  # type: ignore[arg-type]
        )
        self.app.add_exception_handler(
            RequestValidationError, self._handle_validation_error  # type: ignore[arg-type]
        )
        self.app.add_exception_handler(
            Exception, self._handle_unhandled_exception  # type: ignore[arg-type]
        )

    def _get_request_id(self, request: Request) -> Optional[str]:
        """从请求状态中获取请求ID

        Args:
            request: FastAPI请求对象

        Returns:
            请求ID字符串，如果不存在则返回None
        """
        return str(getattr(request.state, "request_id", "") or "").strip() or None

    async def _handle_business_exception(
        self, request: Request, exc: BusinessException
    ) -> JSONResponse:
        """处理业务异常

        处理所有业务逻辑相关的异常，如验证失败、权限不足等。
        根据异常类型返回对应的HTTP状态码。

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

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponseBuilder.build(
                message=exc.message,
                code=exc.code,
                status_code=exc.status_code,
                request_id=request_id,
                details=exc.details,
            ),
            headers=getattr(exc, "headers", None),
        )

    async def _handle_http_exception(
        self, request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """处理HTTP异常

        处理Starlette框架的HTTP异常。
        支持透传自定义响应格式。

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
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "ok": False,
                    "error": {
                        "message": message,
                        "code": detail.get("code", "HTTP_ERROR"),
                        "status": exc.status_code,
                        "ts": int(time.time()),
                        "request_id": request_id,
                        "details": detail.get("details"),
                    },
                    "detail": message,
                },
                headers=exc.headers,
            )

        logger.warning(
            f"HTTP exception: {exc.status_code} - {str(exc.detail)} "
            f"- path: {request.url.path}"
        )

        message = str(exc.detail)
        payload = ErrorResponseBuilder.build(
            message=message,
            code="HTTP_ERROR",
            status_code=exc.status_code,
            request_id=request_id,
        )
        payload["detail"] = message

        return JSONResponse(
            status_code=exc.status_code,
            content=payload,
            headers=exc.headers,
        )

    async def _handle_validation_error(
        self, request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """处理请求验证异常

        处理Pydantic模型验证失败产生的异常。
        提取详细的字段错误信息。

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

        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "error": {
                    "message": "参数验证失败",
                    "code": "VALIDATION_ERROR",
                    "status": 422,
                    "ts": int(time.time()),
                    "request_id": request_id,
                    "details": {
                        "errors": errors,
                    } if self.debug else None,
                }
            },
        )

    async def _handle_unhandled_exception(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """处理未捕获的异常

        处理所有未预期的异常，防止服务崩溃。
        在生产环境中返回通用错误信息。

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

        return JSONResponse(
            status_code=500,
            content=ErrorResponseBuilder.build(
                message="内部服务器错误" if not self.debug else str(exc),
                code="INTERNAL_ERROR",
                status_code=500,
                request_id=request_id,
                details={"exception_type": type(exc).__name__}
                if self.debug else None,
                include_traceback=self.debug,
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
