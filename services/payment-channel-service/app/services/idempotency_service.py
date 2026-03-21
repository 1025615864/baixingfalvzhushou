"""幂等性服务"""
import hashlib
import time
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PaymentCallback


class IdempotencyService:
    """支付回调幂等性服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_processed(self, provider: str, order_no: str) -> bool:
        """检查订单是否已处理"""
        result = await self.db.execute(
            select(PaymentCallback).where(
                PaymentCallback.order_no == order_no,
                PaymentCallback.provider == provider,
            )
        )
        callback = result.scalar_one_or_none()
        return callback is not None

    async def mark_processed(
        self,
        provider: str,
        order_no: str,
        callback_no: Optional[str] = None,
    ) -> None:
        """标记订单已处理"""
        result = await self.db.execute(
            select(PaymentCallback).where(
                PaymentCallback.order_no == order_no,
                PaymentCallback.provider == provider,
            )
        )
        callback = result.scalar_one_or_none()

        if callback:
            callback.processed_at = time.time()
        else:
            callback = PaymentCallback(
                order_no=order_no,
                provider=provider,
                callback_no=callback_no,
                status="processed",
                raw_payload="",
            )
            self.db.add(callback)

        await self.db.commit()
