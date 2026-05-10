"""支付锁工具

提供支付回调的幂等性保护，防止重复处理订单。
"""
import logging
from typing import Any, Callable, Coroutine

from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class PaymentLock:
    """支付锁管理器

    使用Redis分布式锁确保支付回调的幂等性。
    """

    @staticmethod
    async def acquire_lock(order_no: str, expire_seconds: int = 60) -> bool:
        """获取支付锁

        Args:
            order_no: 订单号
            expire_seconds: 锁过期时间（秒）

        Returns:
            是否成功获取锁
        """
        if not cache_service.redis:
            logger.warning("Redis不可用，无法获取分布式锁")
            return False

        lock_key = f"payment:callback:{order_no}"
        
        try:
            # 使用SET NX命令获取锁
            result = await cache_service.redis.set(
                lock_key, "1", nx=True, ex=expire_seconds
            )
            return bool(result)
        except Exception as e:
            logger.error(f"获取支付锁失败: {e}")
            return False

    @staticmethod
    async def release_lock(order_no: str) -> bool:
        """释放支付锁

        Args:
            order_no: 订单号

        Returns:
            是否成功释放锁
        """
        if not cache_service.redis:
            return True

        lock_key = f"payment:callback:{order_no}"
        
        try:
            await cache_service.redis.delete(lock_key)
            return True
        except Exception as e:
            logger.error(f"释放支付锁失败: {e}")
            return False

    @staticmethod
    async def is_locked(order_no: str) -> bool:
        """检查订单是否被锁定

        Args:
            order_no: 订单号

        Returns:
            是否被锁定
        """
        if not cache_service.redis:
            return False

        lock_key = f"payment:callback:{order_no}"
        
        try:
            result = await cache_service.redis.exists(lock_key)
            return bool(result)
        except Exception as e:
            logger.error(f"检查锁状态失败: {e}")
            return False


async def with_payment_lock(order_no: str, func: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs) -> Any:
    """使用支付锁执行函数

    Args:
        order_no: 订单号
        func: 要执行的函数
        *args: 函数参数
        **kwargs: 函数关键字参数

    Returns:
        函数执行结果
    """
    # 尝试获取锁
    if not await PaymentLock.acquire_lock(order_no):
        logger.warning(f"订单 {order_no} 正在处理中，跳过")
        return None

    try:
        # 执行函数
        return await func(*args, **kwargs)
    finally:
        # 释放锁
        await PaymentLock.release_lock(order_no)
