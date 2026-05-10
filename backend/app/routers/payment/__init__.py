from fastapi import APIRouter

router = APIRouter(prefix="/payment", tags=["Payment"])

try:
    from .orders_create import router as orders_create_router
    router.include_router(orders_create_router)
except ImportError:
    pass

try:
    from .orders_pay import router as orders_pay_router
    router.include_router(orders_pay_router)
except ImportError:
    pass

from . import orders_create
from . import orders_pay

__all__ = ["router", "orders_create", "orders_pay"]
