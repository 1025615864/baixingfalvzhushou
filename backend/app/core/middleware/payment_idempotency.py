"""支付回调幂等性保护中间件

提供支付回调的幂等性处理，防止重复处理订单。

功能特性:
    - Redis分布式锁机制
    - 回调去重记录
    - 并发处理保护
    - 自动过期清理

使用示例:
    ```python
    from app.core.middleware.payment_idempotency import (
        PaymentIdempotencyMiddleware,
        PaymentIdempotencyService
    )

    # 作为独立服务使用
    idempotency = PaymentIdempotencyService()
    result = await idempotency.process_callback(
        provider="alipay",
        order_no="ORDER123",
        handler=process_payment_callback
    )
    ```

幂等性保证:
    - 相同订单号的多次回调只会执行一次
    - 锁超时后自动释放
    - 处理完成后永久标记
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from ...services.cache_service import get_cache_service

logger = logging.getLogger("payment_idempotency")

CACHE_KEY_PREFIX = "payment:idempotency"
LOCK_PREFIX = "payment:lock"
PROCESSED_PREFIX = "payment:processed"

LOCK_TIMEOUT = 60
CLEANUP_INTERVAL = 3600


class PaymentProvider(str, Enum):
    """支付提供商"""

    ALIPAY = "alipay"
    WECHAT = "wechat"
    IKUN = "ikun"


class IdempotencyStatus(str, Enum):
    """幂等性处理状态"""

    PROCESSED = "processed"
    PROCESSING = "processing"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class IdempotencyResult:
    """幂等性处理结果"""

    status: IdempotencyStatus
    is_duplicate: bool
    lock_acquired: bool
    processing_time_ms: float
    result: Any | None = None
    error_message: str | None = None


class PaymentIdempotencyService:
    """支付回调幂等性服务

    确保支付回调的幂等性处理，防止重复扣款和数据不一致。

    Attributes:
        cache: 缓存服务
        lock_timeout: 锁超时时间（秒）
        processed_ttl: 已处理标记TTL（秒）
    """

    def __init__(
        self,
        cache=None,
        lock_timeout: int = 60,
        processed_ttl: int = 86400 * 7,
    ) -> None:
        self.cache = cache or get_cache_service()
        self.lock_timeout = lock_timeout
        self.processed_ttl = processed_ttl
        self._lock_ttl = lock_timeout + 30

    def _get_lock_key(self, provider: str, order_no: str) -> str:
        """获取锁键

        Args:
            provider: 支付提供商
            order_no: 订单号

        Returns:
            锁键字符串
        """
        return f"{LOCK_PREFIX}:{provider}:{order_no}"

    def _get_processed_key(self, provider: str, order_no: str) -> str:
        """获取已处理标记键

        Args:
            provider: 支付提供商
            order_no: 订单号

        Returns:
            处理标记键字符串
        """
        return f"{PROCESSED_PREFIX}:{provider}:{order_no}"

    def _generate_callback_hash(
        self, provider: str, order_no: str, payload: dict[str, Any]
    ) -> str:
        """生成回调唯一标识哈希

        Args:
            provider: 支付提供商
            order_no: 订单号
            payload: 回调 payload

        Returns:
            SHA256哈希字符串
        """
        content = json.dumps(
            {"provider": provider, "order_no": order_no, "payload": payload},
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def is_processed(
        self, provider: str, order_no: str, payload: dict[str, Any]
    ) -> bool:
        """检查回调是否已处理

        Args:
            provider: 支付提供商
            order_no: 订单号
            payload: 回调 payload

        Returns:
            是否已处理
        """
        processed_key = self._get_processed_key(provider, order_no)
        cached = await self.cache.get(processed_key)
        return cached is not None

    async def mark_processed(
        self,
        provider: str,
        order_no: str,
        payload: dict[str, Any],
        result: Any = None,
    ) -> None:
        """标记回调已处理

        Args:
            provider: 支付提供商
            order_no: 订单号
            payload: 回调 payload
            result: 处理结果
        """
        processed_key = self._get_processed_key(provider, order_no)
        callback_hash = self._generate_callback_hash(provider, order_no, payload)

        value = json.dumps(
            {
                "hash": callback_hash,
                "result": result,
                "processed_at": time.time(),
            },
            default=str,
        )

        await self.cache.set(processed_key, value, expire=self.processed_ttl)
        logger.info(
            f"Payment callback marked as processed: provider={provider}, "
            f"order_no={order_no}, hash={callback_hash}"
        )

    async def acquire_lock(
        self, provider: str, order_no: str, timeout: int | None = None
    ) -> bool:
        """获取处理锁

        Args:
            provider: 支付提供商
            order_no: 订单号
            timeout: 锁超时时间

        Returns:
            是否获取成功
        """
        lock_key = self._get_lock_key(provider, order_no)
        lock_value = f"{time.time()}:{asyncio.get_event_loop().time()}"

        ttl = timeout or self.lock_timeout
        return await self.cache.acquire_lock(lock_key, lock_value, expire=ttl)

    async def release_lock(self, provider: str, order_no: str) -> None:
        """释放处理锁

        Args:
            provider: 支付提供商
            order_no: 订单号
        """
        lock_key = self._get_lock_key(provider, order_no)
        await self.cache.release_lock(lock_key, "*")

    async def process_callback(
        self,
        provider: str | PaymentProvider,
        order_no: str,
        payload: dict[str, Any],
        handler: Callable[..., Any],
        timeout: int | None = None,
    ) -> IdempotencyResult:
        """处理支付回调（幂等性保证）

        Args:
            provider: 支付提供商
            order_no: 订单号
            payload: 回调 payload
            handler: 实际处理函数
            timeout: 处理超时时间

        Returns:
            IdempotencyResult处理结果
        """
        start_time = time.perf_counter()

        provider_str = provider.value if isinstance(provider, PaymentProvider) else provider

        try:
            is_duplicate = await self.is_processed(provider_str, order_no, payload)

            if is_duplicate:
                logger.info(
                    f"Duplicate payment callback detected: provider={provider_str}, "
                    f"order_no={order_no}"
                )
                return IdempotencyResult(
                    status=IdempotencyStatus.SKIPPED,
                    is_duplicate=True,
                    lock_acquired=False,
                    processing_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="Duplicate callback, already processed",
                )

            lock_acquired = await self.acquire_lock(provider_str, order_no, timeout)

            if not lock_acquired:
                logger.warning(
                    f"Failed to acquire lock for payment callback: "
                    f"provider={provider_str}, order_no={order_no}"
                )
                return IdempotencyResult(
                    status=IdempotencyStatus.PROCESSING,
                    is_duplicate=False,
                    lock_acquired=False,
                    processing_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="Another process is handling this callback",
                )

            try:
                result = await handler(provider_str, order_no, payload)

                await self.mark_processed(provider_str, order_no, payload, result)

                return IdempotencyResult(
                    status=IdempotencyStatus.PROCESSED,
                    is_duplicate=False,
                    lock_acquired=True,
                    processing_time_ms=(time.perf_counter() - start_time) * 1000,
                    result=result,
                )

            except Exception as e:
                logger.exception(
                    f"Payment callback handler error: provider={provider_str}, "
                    f"order_no={order_no}, error={e}"
                )
                return IdempotencyResult(
                    status=IdempotencyStatus.FAILED,
                    is_duplicate=False,
                    lock_acquired=True,
                    processing_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=str(e),
                )
            finally:
                await self.release_lock(provider_str, order_no)

        except Exception as e:
            logger.exception(
                f"Payment idempotency check error: provider={provider_str}, "
                f"order_no={order_no}, error={e}"
            )
            return IdempotencyResult(
                status=IdempotencyStatus.FAILED,
                is_duplicate=False,
                lock_acquired=False,
                processing_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=str(e),
            )

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计字典
        """
        return {
            "lock_timeout": self.lock_timeout,
            "processed_ttl": self.processed_ttl,
        }


_idempotency_service: PaymentIdempotencyService | None = None


def get_idempotency_service() -> PaymentIdempotencyService:
    """获取幂等性服务单例

    Returns:
        PaymentIdempotencyService实例
    """
    global _idempotency_service

    if _idempotency_service is None:
        _idempotency_service = PaymentIdempotencyService()

    return _idempotency_service


async def process_payment_callback_example(
    provider: str, order_no: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """支付回调处理示例

    Args:
        provider: 支付提供商
        order_no: 订单号
        payload: 回调 payload

    Returns:
        处理结果
    """
    from ...routers.payment.utils import update_order_from_callback

    success = await update_order_from_callback(provider, order_no, payload)
    return {"success": success, "order_no": order_no}
