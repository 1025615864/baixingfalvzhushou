from fastapi import APIRouter

from app.config import get_settings

settings = get_settings()

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

try:
    from .callbacks import router as callbacks_router
    router.include_router(callbacks_router)
except ImportError:
    pass

from . import orders_create
from . import orders_pay

try:
    from . import callbacks
except ImportError:
    callbacks = None

try:
    from . import crypto_utils
except ImportError:
    crypto_utils = None

try:
    from .crypto_utils import _alipay_sign_rsa2, _ikunpay_sign_md5
except ImportError:
    _alipay_sign_rsa2 = None
    _ikunpay_sign_md5 = None


async def fetch_platform_certificates():
    return []


__all__ = ["router", "orders_create", "orders_pay", "callbacks", "crypto_utils", "fetch_platform_certificates", "_alipay_sign_rsa2", "_ikunpay_sign_md5"]
