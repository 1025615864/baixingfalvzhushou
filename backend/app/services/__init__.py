"""业务服务

提供基础服务类和服务工厂，支持依赖注入和测试。

使用示例:
    from app.services import BaseService, service_factory

    # 定义服务
    class UserService(BaseService[User]):
        def __init__(self, db: AsyncSession):
            super().__init__(db, User)

    # 注册服务
    service_factory.register("user", UserService)

    # 在路由中使用
    async def get_user_service(db: AsyncSession = Depends(get_db)):
        return service_factory.get("user", db)
"""
from .base import BaseService, ServiceFactory, service_factory

__all__ = ["BaseService", "ServiceFactory", "service_factory"]
