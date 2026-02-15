"""支付路由模块"""
from fastapi import APIRouter

from .orders import router as orders_router
from .orders_pay import router as orders_pay_router
from .callbacks import router as callbacks_router
from .refunds import router as refunds_router
from .cards import router as cards_router
from .admin_config import router as admin_config_router
from .admin_ops import router as admin_ops_router
from .admin_stats import router as admin_stats_router
from .user_ops import router as user_ops_router
from .orders_create import router as orders_create_router

router = APIRouter(prefix="/payment", tags=["支付管理"])

# 包含子路由
router.include_router(orders_router)
router.include_router(orders_pay_router)
router.include_router(callbacks_router)
router.include_router(refunds_router)
router.include_router(cards_router)
router.include_router(admin_config_router)
router.include_router(admin_ops_router)
router.include_router(admin_stats_router)
router.include_router(user_ops_router)
router.include_router(orders_create_router)

__all__ = ["router"]
