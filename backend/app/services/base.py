"""基础服务类

提供通用的服务基类，支持依赖注入和测试。
"""
from __future__ import annotations

import logging
from typing import TypeVar, Generic, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.exceptions import NotFoundException, BusinessException

T = TypeVar("T")
logger = logging.getLogger(__name__)


class BaseService(Generic[T]):
    """基础服务类

    提供通用 CRUD 操作和依赖注入支持。

    使用示例:
        class UserService(BaseService[User]):
            def __init__(self, db: AsyncSession):
                super().__init__(db, User)

            async def get_by_email(self, email: str) -> Optional[User]:
                result = await self.db.execute(
                    select(User).where(User.email == email)
                )
                return result.scalar_one_or_none()

        # 在路由中使用依赖注入
        async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
            return UserService(db)

        @router.get("/users/{user_id}")
        async def get_user(
            user_id: int,
            service: UserService = Depends(get_user_service)
        ):
            return await service.get_one_or_raise(user_id)
    """

    def __init__(self, db: AsyncSession, model_class: type[T]):
        """初始化服务

        Args:
            db: 数据库会话
            model_class: 模型类
        """
        self.db = db
        self.model_class = model_class

    async def get_by_id(self, id: int) -> Optional[T]:
        """根据 ID 获取实体

        Args:
            id: 实体 ID

        Returns:
            实体对象，如果不存在返回 None
        """
        return await self.db.get(self.model_class, id)

    async def get_one_or_raise(
        self,
        id: int,
        message: Optional[str] = None
    ) -> T:
        """根据 ID 获取实体，不存在则抛出异常

        Args:
            id: 实体 ID
            message: 自定义错误消息

        Returns:
            实体对象

        Raises:
            NotFoundException: 实体不存在
        """
        entity = await self.get_by_id(id)
        if entity is None:
            model_name = self.model_class.__name__
            raise NotFoundException(
                message or f"{model_name} with id {id} not found"
            )
        return entity

    async def create(self, **kwargs: Any) -> T:
        """创建实体

        Args:
            **kwargs: 实体属性

        Returns:
            创建的实体
        """
        entity = self.model_class(**kwargs)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: T, **kwargs: Any) -> T:
        """更新实体

        Args:
            entity: 实体对象
            **kwargs: 要更新的属性

        Returns:
            更新后的实体
        """
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: T) -> None:
        """删除实体

        Args:
            entity: 实体对象
        """
        await self.db.delete(entity)
        await self.db.flush()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None
    ) -> list[T]:
        """获取实体列表

        Args:
            skip: 跳过数量
            limit: 返回数量限制
            order_by: 排序字段

        Returns:
            实体列表
        """
        query = select(self.model_class)

        if order_by is not None:
            query = query.order_by(order_by)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self) -> int:
        """获取实体总数

        Returns:
            实体数量
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count()).select_from(self.model_class)
        )
        return result.scalar() or 0


class ServiceFactory:
    """服务工厂

    用于创建服务实例，支持依赖注入和测试模拟。

    使用示例:
        factory = ServiceFactory()

        # 注册服务
        factory.register("user", UserService)

        # 获取服务
        user_service = await factory.get("user", db)

        # 在测试中模拟
        factory.override("user", mock_user_service)
    """

    def __init__(self):
        self._services: dict[str, type[BaseService]] = {}
        self._overrides: dict[str, BaseService] = {}

    def register(self, name: str, service_class: type[BaseService]) -> None:
        """注册服务

        Args:
            name: 服务名称
            service_class: 服务类
        """
        self._services[name] = service_class

    def override(self, name: str, service: BaseService) -> None:
        """覆盖服务（用于测试）

        Args:
            name: 服务名称
            service: 服务实例
        """
        self._overrides[name] = service

    def clear_override(self, name: str) -> None:
        """清除覆盖

        Args:
            name: 服务名称
        """
        self._overrides.pop(name, None)

    def get(self, name: str, db: AsyncSession) -> BaseService:
        """获取服务实例

        Args:
            name: 服务名称
            db: 数据库会话

        Returns:
            服务实例

        Raises:
            ValueError: 服务未注册
        """
        # 检查是否有覆盖（用于测试）
        if name in self._overrides:
            return self._overrides[name]

        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")

        return self._services[name](db)


# 全局服务工厂实例
service_factory = ServiceFactory()
