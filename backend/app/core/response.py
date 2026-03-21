"""统一API响应格式模块

提供标准化的API响应结构和辅助函数，确保所有API响应格式一致。

新版响应格式规范 (success/message/data/error_code):
    成功响应:
        {
            "success": true,
            "message": "操作成功",
            "data": {...},
            "error_code": null
        }

    分页响应:
        {
            "success": true,
            "message": "操作成功",
            "data": [...],
            "error_code": null,
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total": 100,
                "total_pages": 5
            }
        }

    错误响应:
        {
            "success": false,
            "message": "资源不存在",
            "data": null,
            "error_code": 1004
        }

使用示例:
    ```python
    from app.core.response import ApiResponse, PaginatedResponse, api_response, paginated_response

    # 使用响应类
    @app.get("/users/{user_id}")
    async def get_user(user_id: int) -> ApiResponse[UserSchema]:
        user = await get_user_by_id(user_id)
        if not user:
            return ApiResponse(success=False, message="用户不存在", error_code=ErrorCode.NOT_FOUND)
        return ApiResponse(success=True, message="获取成功", data=user)

    # 使用工具函数
    @app.get("/users")
    async def list_users(
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResponse[UserSchema]:
        users, total = await get_users_paginated(page, page_size)
        return paginated_response(users, page, page_size, total)
    ```
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")
T2 = TypeVar("T2")


# ============================================================
# 新版 Pydantic 响应模型 (使用 success/message/data/error_code)
# ============================================================


class ErrorCode(IntEnum):
    """业务错误码枚举 (整数形式)

    错误码范围分配:
        - 通用错误: 1000-1999
        - 用户相关: 2000-2999
        - 支付相关: 3000-3999
        - AI相关: 4000-4999
        - 业务相关: 5000-5999
        - 内容相关: 6000-6999
        - 论坛相关: 7000-7999
        - 系统相关: 8000-8999
        - 限流相关: 9000-9999
    """

    # 通用错误 1000-1999
    SUCCESS = 0
    INVALID_PARAMS = 1001
    UNAUTHORIZED = 1002
    FORBIDDEN = 1003
    NOT_FOUND = 1004
    INTERNAL_ERROR = 1005
    CONFLICT = 1006
    VALIDATION_ERROR = 1007
    RATE_LIMIT_EXCEEDED = 1008
    SERVICE_UNAVAILABLE = 1009

    # 用户相关 2000-2999
    USER_NOT_FOUND = 2001
    USER_ALREADY_EXISTS = 2002
    INVALID_CREDENTIALS = 2003
    TOKEN_EXPIRED = 2004
    TOKEN_INVALID = 2005
    EMAIL_VERIFICATION_REQUIRED = 2006
    PHONE_VERIFICATION_REQUIRED = 2007

    # 支付相关 3000-3999
    PAYMENT_FAILED = 3001
    PAYMENT_AMOUNT_MISMATCH = 3002
    PAYMENT_ORDER_NOT_FOUND = 3003
    PAYMENT_ORDER_ALREADY_PAID = 3004
    PAYMENT_ORDER_CANCELLED = 3005
    PAYMENT_CALLBACK_INVALID = 3006
    PAYMENT_CALLBACK_DUPLICATE = 3007
    PAYMENT_METHOD_NOT_SUPPORTED = 3008
    PAYMENT_PROCESSING_ERROR = 3009
    PAYMENT_TIMEOUT = 3010
    INSUFFICIENT_BALANCE = 3011

    # AI相关 4000-4999
    AI_SERVICE_UNAVAILABLE = 4001
    AI_QUOTA_EXCEEDED = 4002
    AI_REQUEST_TOO_LONG = 4003
    AI_RESPONSE_INVALID = 4004
    AI_TIMEOUT = 4005
    AI_RATE_LIMIT_EXCEEDED = 4006

    # 业务相关 5000-5999
    INVALID_ORDER_TYPE = 5001
    ORDER_EXPIRED = 5002
    RESOURCE_NOT_FOUND = 5003
    RESOURCE_ALREADY_EXISTS = 5004
    OPERATION_NOT_ALLOWED = 5005

    # 内容相关 6000-6999
    CONTENT_NOT_FOUND = 6001
    CONTENT_ALREADY_PUBLISHED = 6002
    CONTENT_MODIFICATION_NOT_ALLOWED = 6003
    CONTENT_VALIDATION_FAILED = 6004

    # 论坛相关 7000-7999
    FORUM_POST_NOT_FOUND = 7001
    FORUM_COMMENT_NOT_FOUND = 7002
    FORUM_POST_LOCKED = 7003
    FORUM_COMMENT_NOT_ALLOWED = 7004

    # 系统相关 8000-8999
    SYSTEM_MAINTENANCE = 8001
    SYSTEM_OVERLOADED = 8002
    DATABASE_ERROR = 8003
    CACHE_ERROR = 8004
    EXTERNAL_SERVICE_ERROR = 8005


class PaginationInfo(BaseModel):
    """分页信息

    Attributes:
        page: 当前页码 (从1开始)
        page_size: 每页大小
        total: 总记录数
        total_pages: 总页数
    """

    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total: int = Field(..., description="总记录数")
    total_pages: int = Field(..., description="总页数")


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式

    使用 success/message/data/error_code 字段的标准响应格式。

    Attributes:
        success: 请求是否成功
        message: 响应消息
        data: 响应数据 (可选)
        error_code: 错误码 (成功时为None)

    Examples:
        ```python
        # 成功响应
        ApiResponse(success=True, message="获取成功", data={"id": 1})

        # 错误响应
        ApiResponse(success=False, message="用户不存在", error_code=ErrorCode.NOT_FOUND)
        ```
    """

    success: bool = Field(..., description="请求是否成功")
    message: str = Field(default="Success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    error_code: Optional[int] = Field(default=None, description="错误码")

    class Config:
        arbitrary_types_allowed = True


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式

    用于列表接口的分页响应，包含数据列表和分页信息。

    Attributes:
        success: 请求是否成功
        message: 响应消息
        data: 数据列表
        pagination: 分页信息

    Examples:
        ```python
        PaginatedResponse(
            success=True,
            message="获取成功",
            data=[{"id": 1}, {"id": 2}],
            pagination=PaginationInfo(page=1, page_size=20, total=100, total_pages=5)
        )
        ```
    """

    success: bool = Field(..., description="请求是否成功")
    message: str = Field(default="Success", description="响应消息")
    data: List[T] = Field(default_factory=list, description="数据列表")
    pagination: PaginationInfo = Field(..., description="分页信息")

    class Config:
        arbitrary_types_allowed = True


# ============================================================
# 响应工具函数 (兼容新版格式)
# ============================================================


def api_response(
    data: Any = None,
    message: str = "Success",
    success: bool = True,
    error_code: Optional[int] = None,
) -> dict[str, Any]:
    """创建API响应 (新格式)

    使用 success/message/data/error_code 格式创建响应。

    Args:
        data: 响应数据
        message: 响应消息
        success: 是否成功
        error_code: 错误码 (失败时必填)

    Returns:
        标准响应字典

    Examples:
        ```python
        # 成功响应
        return api_response(data={"id": 1}, message="获取成功")

        # 错误响应
        return api_response(
            success=False,
            message="用户不存在",
            error_code=ErrorCode.NOT_FOUND
        )
        ```
    """
    result: dict[str, Any] = {
        "success": success,
        "message": message,
        "data": data,
    }
    if error_code is not None:
        result["error_code"] = error_code
    return result


def paginated_response(
    items: List[Any],
    page: int,
    page_size: int,
    total: int,
    message: str = "Success",
) -> dict[str, Any]:
    """创建分页响应 (新格式)

    Args:
        items: 数据列表
        page: 当前页码
        page_size: 每页大小
        total: 总记录数
        message: 响应消息

    Returns:
        分页响应字典
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "success": True,
        "message": message,
        "data": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }


def error_response(
    message: str,
    error_code: int,
    data: Any = None,
) -> dict[str, Any]:
    """创建错误响应 (新格式)

    Args:
        message: 错误消息
        error_code: 错误码
        data: 额外的错误数据

    Returns:
        错误响应字典
    """
    result: dict[str, Any] = {
        "success": False,
        "message": message,
        "data": data,
        "error_code": error_code,
    }
    return result


def success_response(
    data: Any = None,
    message: str = "Success",
) -> dict[str, Any]:
    """创建成功响应 (新格式)

    Args:
        data: 响应数据
        message: 成功消息

    Returns:
        成功响应字典
    """
    return api_response(data=data, message=message, success=True, error_code=None)


# ============================================================
# 旧版响应类 (向后兼容 - 使用 ok/data/ts)
# ============================================================


@dataclass
class APIResponse(Generic[T]):
    """标准API响应结构

    所有API响应的基础数据结构。

    Attributes:
        ok: 是否成功，默认为True
        data: 响应数据，可以是任意类型
        ts: 时间戳，默认为当前时间

    Examples:
        ```python
        response = APIResponse(
            ok=True,
            data={"user_id": 123, "name": "张三"},
            ts=1699999999
        )
        # 输出: {"ok": true, "data": {"user_id": 123, "name": "张三"}, "ts": 1699999999}
        ```
    """

    ok: bool = True
    data: Optional[T] = None
    ts: int = field(default_factory=lambda: int(time.time()))

    def to_dict(self) -> dict[str, Any]:
        """转换为字典

        Returns:
            标准响应字典
        """
        result: dict[str, Any] = {
            "ok": self.ok,
            "ts": self.ts,
        }
        if self.data is not None:
            result["data"] = self.data
        return result


@dataclass
class APIError:
    """标准错误响应结构

    用于构建标准化的错误响应。

    Attributes:
        message: 错误描述信息
        code: 错误码
        status: HTTP状态码
        ts: 时间戳
        request_id: 请求ID（可选）
        details: 额外详情（可选）

    Examples:
        ```python
        error = APIError(
            message="用户不存在",
            code="USER_NOT_FOUND",
            status=404,
            request_id="req_123",
            details={"user_id": 123}
        )
        ```
    """

    message: str
    code: str
    status: int
    ts: int = field(default_factory=lambda: int(time.time()))
    request_id: Optional[str] = None
    details: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典

        Returns:
            错误响应字典
        """
        result: dict[str, Any] = {
            "ok": False,
            "error": {
                "message": self.message,
                "code": self.code,
                "status": self.status,
                "ts": self.ts,
            }
        }
        if self.request_id:
            result["error"]["request_id"] = self.request_id
        if self.details:
            result["error"]["details"] = self.details
        return result


@dataclass
class SuccessResponse(Generic[T]):
    """成功响应包装器

    用于快速创建成功响应的数据结构。

    Attributes:
        data: 响应数据
        message: 可选的成功消息

    Examples:
        ```python
        response = SuccessResponse(
            data={"user_id": 123},
            message="获取成功"
        )
        # 输出: {"ok": true, "data": {"user_id": 123}, "message": "获取成功", "ts": 1699999999}
        ```
    """

    data: T
    message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典

        Returns:
            成功响应字典
        """
        result: dict[str, Any] = {
            "ok": True,
            "data": self.data,
            "ts": int(time.time()),
        }
        if self.message:
            result["message"] = self.message
        return result


@dataclass
class ListResponse(Generic[T]):
    """列表响应包装器

    用于创建分页列表响应的数据结构。

    Attributes:
        items: 数据列表
        total: 总记录数（可选）
        page: 当前页码（可选）
        page_size: 每页大小（可选）

    Examples:
        ```python
        response = ListResponse(
            items=[{"id": 1}, {"id": 2}],
            total=100,
            page=1,
            page_size=20
        )
        # 输出: {"ok": true, "data": {"items": [...], "total": 100, "page": 1, "page_size": 20}, "ts": 1699999999}
        ```
    """

    items: list[T]
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典

        Returns:
            列表响应字典
        """
        result: dict[str, Any] = {
            "ok": True,
            "data": {
                "items": self.items,
            },
            "ts": int(time.time()),
        }
        if self.total is not None:
            result["data"]["total"] = self.total
        if self.page is not None:
            result["data"]["page"] = self.page
        if self.page_size is not None:
            result["data"]["page_size"] = self.page_size
        return result


class ResponseFactory:
    """响应工厂类

    提供便捷的静态方法快速创建各类响应。

    所有方法返回标准化的字典格式，可直接作为FastAPI响应返回。

    Examples:
        ```python
        from app.core.response import ResponseFactory

        # 成功响应
        return ResponseFactory.success({"id": 1})

        # 创建成功
        return ResponseFactory.created({"id": 1})

        # 更新成功
        return ResponseFactory.updated({"id": 1})

        # 删除成功
        return ResponseFactory.deleted()

        # 列表响应
        return ResponseFactory.list(items=[], total=0)

        # 错误响应
        return ResponseFactory.error(
            message="用户不存在",
            code="USER_NOT_FOUND",
            status_code=404
        )
        ```
    """

    @staticmethod
    def success(
        data: Any = None, message: Optional[str] = None
    ) -> dict[str, Any]:
        """创建成功响应

        Args:
            data: 响应数据
            message: 可选的成功消息

        Returns:
            成功响应字典
        """
        return SuccessResponse(data=data, message=message).to_dict()

    @staticmethod
    def created(
        data: Any = None, message: Optional[str] = "创建成功"
    ) -> dict[str, Any]:
        """创建资源成功响应

        用于POST创建资源成功后的响应。

        Args:
            data: 创建的资源数据
            message: 成功消息

        Returns:
            成功响应字典
        """
        return SuccessResponse(data=data, message=message).to_dict()

    @staticmethod
    def updated(
        data: Any = None, message: Optional[str] = "更新成功"
    ) -> dict[str, Any]:
        """更新资源成功响应

        用于PUT/PATCH更新资源成功后的响应。

        Args:
            data: 更新后的资源数据
            message: 成功消息

        Returns:
            成功响应字典
        """
        return SuccessResponse(data=data, message=message).to_dict()

    @staticmethod
    def deleted(message: Optional[str] = "删除成功") -> dict[str, Any]:
        """删除资源成功响应

        用于DELETE删除资源成功后的响应。

        Args:
            message: 成功消息

        Returns:
            成功响应字典
        """
        return SuccessResponse(data=None, message=message).to_dict()

    @staticmethod
    def list(
        items: list[Any],
        total: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> dict[str, Any]:
        """创建列表响应

        用于GET列表接口的响应，支持分页信息。

        Args:
            items: 数据列表
            total: 总记录数
            page: 当前页码
            page_size: 每页大小

        Returns:
            列表响应字典
        """
        return ListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        ).to_dict()

    @staticmethod
    def error(
        message: str,
        code: str,
        status_code: int,
        request_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """创建错误响应

        用于创建标准化的错误响应。

        Args:
            message: 错误描述
            code: 错误码
            status_code: HTTP状态码
            request_id: 请求ID
            details: 额外详情

        Returns:
            错误响应字典
        """
        error = APIError(
            message=message,
            code=code,
            status=status_code,
            request_id=request_id,
            details=details,
        )
        return error.to_dict()
