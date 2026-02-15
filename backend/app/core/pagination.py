"""分页参数和响应模块

提供标准化的分页功能支持，包括分页参数解析、分页响应构建等。

分页参数:
    - page: 当前页码，从1开始
    - page_size: 每页数量，默认20，最大100

分页响应格式:
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

使用示例:
    ```python
    from fastapi import Query
    from app.core.pagination import PaginationParams, paginated_response

    @app.get("/users")
    async def list_users(
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100)
    ):
        params = PaginationParams(page=page, page_size=page_size)
        users, total = await get_users(offset=params.offset, limit=params.limit)
        return paginated_response(users, params, total)
    ```
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .response import ListResponse


@dataclass
class PaginationParams:
    """分页参数类

    用于存储和管理分页参数，支持自动校验和边界处理。

    参数规则:
        - page: 最小值为1，小于1时自动调整为1
        - page_size: 最小值为1，最大值为100，超出范围自动调整

    Attributes:
        page: 当前页码
        page_size: 每页数量

    Examples:
        ```python
        # 正常情况
        params = PaginationParams(page=2, page_size=30)
        print(params.offset)  # 30
        print(params.limit)   # 30

        # 超出范围自动调整
        params = PaginationParams(page=-1, page_size=200)
        print(params.page)      # 1
        print(params.page_size) # 100
        ```
    """

    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = 1
        if self.page_size > 100:
            self.page_size = 100

    @property
    def offset(self) -> int:
        """计算数据库查询偏移量

        Returns:
            偏移量 = (页码 - 1) * 每页数量
        """
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """获取每页限制数量

        Returns:
            每页数量
        """
        return self.page_size


def paginated_response(
    items: list[Any],
    pagination: PaginationParams,
    total: int,
) -> ListResponse:
    """创建分页响应

    将数据列表、分页参数和总数组合并为标准分页响应。

    Args:
        items: 当前页的数据列表
        pagination: 分页参数对象
        total: 总记录数

    Returns:
        ListResponse分页响应对象，可直接转换为字典

    Examples:
        ```python
        params = PaginationParams(page=2, page_size=20)
        users, total = await get_users(offset=40, limit=20)
        response = paginated_response(users, params, total)
        return response.to_dict()
        ```
    """
    return ListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


def get_pagination_from_query(
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> PaginationParams:
    """从查询参数创建分页对象

    从FastAPI查询参数创建分页对象，未提供参数时使用默认值。

    Args:
        page: 页码查询参数
        page_size: 每页数量查询参数

    Returns:
        PaginationParams分页参数对象

    Examples:
        ```python
        # FastAPI路由中使用
        @app.get("/users")
        async def list_users(
            page: int = 1,
            page_size: int = 20
        ):
            params = get_pagination_from_query(page, page_size)
            # 或使用默认值
            params = get_pagination_from_query()
            # params.page = 1, params.page_size = 20
        ```
    """
    return PaginationParams(
        page=page or 1,
        page_size=page_size or 20,
    )
