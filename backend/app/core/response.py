"""统一API响应格式模块

提供标准化的API响应结构和辅助函数，确保所有API响应格式一致。

响应格式规范:
    成功响应:
        {
            "ok": true,
            "data": {...},
            "ts": 1699999999,
            "message": "操作成功"  // 可选
        }

    列表响应:
        {
            "ok": true,
            "data": {
                "items": [...],
                "total": 100,
                "page": 1,
                "page_size": 20
            },
            "ts": 1699999999
        }

    错误响应:
        {
            "ok": false,
            "error": {
                "message": "资源不存在",
                "code": "NOT_FOUND",
                "status": 404,
                "ts": 1699999999,
                "request_id": "req_abc123",  // 可选
                "details": {...}              // 可选
            }
        }

使用示例:
    ```python
    from app.core.response import ResponseFactory, SuccessResponse, ListResponse

    # 使用工厂方法
    @app.get("/users/{user_id}")
    async def get_user(user_id: int) -> dict:
        user = await get_user_by_id(user_id)
        if not user:
            return ResponseFactory.error(
                message="用户不存在",
                code="USER_NOT_FOUND",
                status_code=404
            )
        return ResponseFactory.success(data=user)

    # 使用数据类
    @app.get("/users")
    async def list_users() -> dict:
        users = await get_users()
        return ResponseFactory.list(
            items=users,
            total=len(users),
            page=1,
            page_size=20
        )
    ```
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


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
