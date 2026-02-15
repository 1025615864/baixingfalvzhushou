"""统一异常处理模块

提供标准化的业务异常和系统异常定义，支持错误码、错误信息和详细信息标准化。
所有异常都遵循统一的格式，便于前端解析和用户提示。

异常体系:
    BaseException
    ├── BusinessException (业务异常，带HTTP状态码)
    │   ├── NotFoundException (404)
    │   ├── ForbiddenException (403)
    │   ├── UnauthorizedException (401)
    │   ├── ValidationException (422)
    │   ├── ConflictException (409)
    │   ├── RateLimitException (429)
    │   └── PaymentException (400)
    ├── DatabaseException (数据库异常)
    └── ExternalServiceException (外部服务异常)

使用示例:
    ```python
    from app.core import NotFoundException, ValidationException

    # 抛出资源不存在异常
    raise NotFoundException(
        message="用户不存在",
        code="USER_NOT_FOUND",
        details={"user_id": 123}
    )

    # 抛出参数验证异常
    raise ValidationException(
        message="邮箱格式不正确",
        code="INVALID_EMAIL",
        details={"field": "email", "value": "invalid"}
    )
    ```

异常响应格式:
    ```json
    {
        "message": "资源不存在",
        "code": "NOT_FOUND",
        "details": {"user_id": 123}
    }
    ```
"""
from __future__ import annotations

from typing import Any, Optional
from fastapi import HTTPException, status


class BaseException(Exception):
    """基础异常类

    所有自定义异常的基类，提供统一的错误信息、错误码和详细信息结构。

    Attributes:
        message: 错误描述信息，面向用户显示
        code: 错误码，用于程序识别（默认为类名大写）
        details: 额外详细信息，用于调试和问题排查
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.code = code or self.__class__.__name__.upper()
        self.details = details or {}
        super().__init__(self.message)


class BusinessException(BaseException):
    """业务逻辑异常

    用于业务规则验证失败、数据状态异常等业务层面的错误。
    继承自BaseException，并添加了HTTP状态码支持。

    Attributes:
        message: 错误描述信息
        code: 错误码标识
        details: 额外详细信息
        status_code: HTTP状态码（默认400）
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(message, code, details)
        self.status_code = status_code


class NotFoundException(BusinessException):
    """资源不存在异常

    当请求的资源（用户、订单、文件等）不存在时抛出。
    默认HTTP状态码：404

    Examples:
        ```python
        raise NotFoundException(
            message="订单不存在",
            code="ORDER_NOT_FOUND",
            details={"order_id": "ORD-123"}
        )
        ```
    """

    def __init__(
        self,
        message: str = "资源不存在",
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message, code or "NOT_FOUND", details,
            status.HTTP_404_NOT_FOUND
        )


class ForbiddenException(BusinessException):
    """权限不足异常

    当用户尝试访问无权限的资源或执行无权限的操作时抛出。
    默认HTTP状态码：403

    Examples:
        ```python
        raise ForbiddenException(
            message="无权访问此订单",
            code="ACCESS_DENIED",
            details={"resource": "order", "resource_id": "ORD-123"}
        )
        ```
    """

    def __init__(
        self,
        message: str = "权限不足",
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message, code or "FORBIDDEN", details,
            status.HTTP_403_FORBIDDEN
        )


class UnauthorizedException(BusinessException):
    """未认证异常

    当请求需要认证但未提供有效凭证时抛出。
    默认HTTP状态码：401

    Examples:
        ```python
        raise UnauthorizedException(
            message="登录已过期，请重新登录",
            code="TOKEN_EXPIRED"
        )
        ```
    """

    def __init__(
        self,
        message: str = "未认证",
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message, code or "UNAUTHORIZED", details,
            status.HTTP_401_UNAUTHORIZED
        )


class ValidationException(BusinessException):
    """参数验证异常

    当请求参数不符合验证规则时抛出。
    默认HTTP状态码：422

    Attributes:
        errors: 详细的验证错误信息列表

    Examples:
        ```python
        raise ValidationException(
            message="参数验证失败",
            code="INVALID_INPUT",
            details={"errors": [
                {"field": "email", "message": "邮箱格式不正确"},
                {"field": "age", "message": "年龄必须大于18"}
            ]}
        )
        ```
    """

    def __init__(
        self,
        message: str = "参数验证失败",
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message, code or "VALIDATION_ERROR", details,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class ConflictException(BusinessException):
    """资源冲突异常

    当操作与资源当前状态冲突时抛出，如重复提交、资源已存在等。
    默认HTTP状态码：409

    Examples:
        ```python
        raise ConflictException(
            message="邮箱已被注册",
            code="EMAIL_CONFLICT",
            details={"field": "email", "value": "user@example.com"}
        )
        ```
    """

    def __init__(
        self,
        message: str = "资源冲突",
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message, code or "CONFLICT", details,
            status.HTTP_409_CONFLICT
        )


class RateLimitException(BusinessException):
    """请求频率限制异常

    当用户请求频率超过限制时抛出。
    默认HTTP状态码：429

    Attributes:
        retry_after: 建议重试的等待时间（秒）
        limit: 当前请求限制数量
        window: 时间窗口（秒）

    Examples:
        ```python
        raise RateLimitException(
            message="请求过于频繁，请稍后再试",
            code="RATE_LIMIT_EXCEEDED",
            retry_after=60,
            details={"limit": 100, "window": 60}
        )
        ```
    """

    def __init__(
        self,
        message: str = "请求过于频繁",
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        retry_after: int = 60,
    ) -> None:
        super().__init__(
            message, code or "RATE_LIMIT", details,
            status.HTTP_429_TOO_MANY_REQUESTS
        )
        self.retry_after = retry_after


class PaymentException(BusinessException):
    """支付相关异常

    当支付流程中出现错误时抛出，如支付失败、余额不足等。
    默认HTTP状态码：400

    Examples:
        ```python
        raise PaymentException(
            message="支付失败，余额不足",
            code="INSUFFICIENT_BALANCE",
            details={"required": 100.00, "available": 50.00}
        )
        ```
    """

    def __init__(
        self,
        message: str = "支付处理失败",
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message, code or "PAYMENT_ERROR", details,
            status.HTTP_400_BAD_REQUEST
        )


class DatabaseException(BaseException):
    """数据库操作异常

    当数据库操作（查询、插入、更新、删除）失败时抛出。
    不直接对应HTTP状态码，由异常处理器转换为500。

    Examples:
        ```python
        raise DatabaseException(
            message="数据库连接失败",
            code="DB_CONNECTION_ERROR",
            details={"operation": "connect", "database": "primary"}
        )
        ```
    """

    def __init__(
        self,
        message: str = "数据库操作失败",
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code or "DATABASE_ERROR", details)


class ExternalServiceException(BaseException):
    """外部服务调用异常

    当调用外部服务（第三方API、支付网关、短信服务等）失败时抛出。
    不直接对应HTTP状态码，由异常处理器根据情况转换。

    Attributes:
        message: 错误描述
        code: 错误码
        details: 额外详情
        service_name: 外部服务名称
        response_status: 外部服务返回的状态码

    Examples:
        ```python
        raise ExternalServiceException(
            message="微信支付接口调用失败",
            code="WECHAT_PAY_ERROR",
            service_name="wechat_pay",
            details={
                "error_code": "SYSTEM_ERROR",
                "response": {"err_code_des": "系统错误"}
            }
        )
        ```
    """

    def __init__(
        self,
        message: str = "外部服务调用失败",
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        service_name: Optional[str] = None,
        response_status: Optional[int] = None,
    ) -> None:
        super().__init__(message, code or "EXTERNAL_SERVICE_ERROR", details)
        self.service_name = service_name
        self.response_status = response_status


def http_exception_from_business_exception(
    exc: BusinessException
) -> HTTPException:
    """将业务异常转换为FastAPI HTTPException

    用于在异常自定义业务处理器中将异常转换为FastAPI可识别的HTTPException。
    支持自动设置RateLimit异常的Retry-After头。

    Args:
        exc: 业务异常实例

    Returns:
        FastAPI HTTPException实例

    Examples:
        ```python
        from app.core.exceptions import http_exception_from_business_exception

        try:
            raise NotFoundException("用户不存在")
        except BaseException as e:
            http_exc = http_exception_from_business_exception(e)
            raise http_exc
        ```
    """
    headers = None
    if isinstance(exc, RateLimitException):
        headers = {"Retry-After": str(exc.retry_after)}

    return HTTPException(
        status_code=exc.status_code,
        detail={
            "message": exc.message,
            "code": exc.code,
            "details": exc.details,
        },
        headers=headers,
    )
