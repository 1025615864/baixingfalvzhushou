"""订单定时任务

提供订单超时自动取消等定时任务功能。
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_db
from ..models.payment import PaymentOrder, PaymentStatus
from ..services.notification_service import notification_service
from ..utils.structured_logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def cancel_expired_orders():
    """取消过期订单

    取消24小时内未支付的订单。
    """
    async with get_db() as db:
        try:
            # 查询过期订单
            expired_time = datetime.now(timezone.utc) - timedelta(hours=24)
            result = await db.execute(
                select(PaymentOrder).where(
                    PaymentOrder.status == PaymentStatus.PENDING,
                    PaymentOrder.created_at < expired_time
                )
            )
            orders = result.scalars().all()

            if not orders:
                logger.info("没有需要取消的过期订单")
                return

            # 取消订单
            canceled_count = 0
            for order in orders:
                order.status = PaymentStatus.CANCELLED
                order.cancelled_at = datetime.now(timezone.utc)
                order.cancel_reason = "订单超时自动取消"
                canceled_count += 1

            await db.commit()

            logger.info(f"已取消 {canceled_count} 个过期订单")

            # 发送通知
            for order in orders:
                try:
                    await notification_service.send_notification(
                        user_id=order.user_id,
                        title="订单已取消",
                        message=f"订单 {order.order_no} 因超时已自动取消",
                        notification_type="order_cancelled",
                        metadata={"order_no": order.order_no}
                    )
                except Exception as e:
                    logger.error(f"发送订单取消通知失败: {e}")

        except Exception as e:
            logger.error(f"取消过期订单失败: {e}")
            await db.rollback()


async def check_pending_orders():
    """检查待支付订单

    定期检查待支付订单的状态，用于监控和告警。
    """
    async with get_db() as db:
        try:
            # 查询待支付订单
            result = await db.execute(
                select(PaymentOrder).where(
                    PaymentOrder.status == PaymentStatus.PENDING
                )
            )
            orders = result.scalars().all()

            if not orders:
                logger.info("没有待支付订单")
                return

            # 统计订单创建时间分布
            now = datetime.now(timezone.utc)
            pending_counts = {
                "1小时内": 0,
                "1-6小时": 0,
                "6-24小时": 0,
                "24小时以上": 0,
            }

            for order in orders:
                age = now - order.created_at
                if age < timedelta(hours=1):
                    pending_counts["1小时内"] += 1
                elif age < timedelta(hours=6):
                    pending_counts["1-6小时"] += 1
                elif age < timedelta(hours=24):
                    pending_counts["6-24小时"] += 1
                else:
                    pending_counts["24小时以上"] += 1

            logger.info(f"待支付订单统计: {pending_counts}")

        except Exception as e:
            logger.error(f"检查待支付订单失败: {e}")


async def cleanup_cancelled_orders():
    """清理已取消订单

    清理30天前已取消的订单，释放存储空间。
    """
    async with get_db() as db:
        try:
            # 查询30天前的已取消订单
            cleanup_time = datetime.now(timezone.utc) - timedelta(days=30)
            result = await db.execute(
                select(PaymentOrder).where(
                    PaymentOrder.status == PaymentStatus.CANCELLED,
                    PaymentOrder.cancelled_at < cleanup_time
                )
            )
            orders = result.scalars().all()

            if not orders:
                logger.info("没有需要清理的已取消订单")
                return

            # 删除订单
            for order in orders:
                await db.delete(order)

            await db.commit()

            logger.info(f"已清理 {len(orders)} 个已取消订单")

        except Exception as e:
            logger.error(f"清理已取消订单失败: {e}")
            await db.rollback()
