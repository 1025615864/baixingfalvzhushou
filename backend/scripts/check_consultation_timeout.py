"""咨询超时自动取消定时任务

检查超时的待处理咨询，自动取消并发送通知
超时时间：24小时未接单自动取消
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models.lawfirm import LawyerConsultation
from app.models.notification import Notification, NotificationType
from app.models.payment import PaymentOrder, PaymentStatus, UserBalance, BalanceTransaction
from app.models.user import User


# 超时时间：24小时
TIMEOUT_HOURS = 24


async def check_consultation_timeout():
    """检查并取消超时的待处理咨询"""
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker() as db:
        # 计算超时时间点
        timeout_threshold = datetime.now(timezone.utc) - timedelta(hours=TIMEOUT_HOURS)

        # 查找超时的待处理咨询
        result = await db.execute(
            select(LawyerConsultation)
            .where(
                LawyerConsultation.status == "pending",
                LawyerConsultation.created_at < timeout_threshold,
            )
        )
        consultations = result.scalars().all()

        if not consultations:
            print(f"[{datetime.now(timezone.utc)}] 没有超时的待处理咨询")
            return

        print(f"[{datetime.now(timezone.utc)}] 发现 {len(consultations)} 个超时的待处理咨询")

        for consultation in consultations:
            try:
                # 获取关联的支付订单
                order_result = await db.execute(
                    select(PaymentOrder)
                    .where(
                        PaymentOrder.related_type == "lawyer_consultation",
                        PaymentOrder.related_id == consultation.id,
                    )
                    .order_by(PaymentOrder.created_at.desc())
                    .limit(1)
                )
                order = order_result.scalar_one_or_none()

                # 处理退款（如果已支付）
                if order and order.status == PaymentStatus.PAID:
                    if str(order.payment_method or "").lower() == "balance":
                        # 余额支付，执行退款
                        from decimal import Decimal, ROUND_HALF_UP

                        refund_amount = Decimal(str(order.actual_amount)).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                        refund_amount_cents = int(refund_amount * 100)

                        # 更新订单状态
                        await db.execute(
                            update(PaymentOrder)
                            .where(PaymentOrder.id == order.id)
                            .values(status=PaymentStatus.REFUNDED)
                        )

                        # 更新用户余额
                        bal_res = await db.execute(
                            select(UserBalance).where(UserBalance.user_id == order.user_id)
                        )
                        balance_account = bal_res.scalar_one_or_none()

                        if balance_account is None:
                            balance_account = UserBalance(
                                user_id=int(order.user_id),
                                balance=0.0,
                                frozen=0.0,
                                total_recharged=0.0,
                                total_consumed=0.0,
                            )
                            db.add(balance_account)
                            await db.flush()

                        balance_before = Decimal(str(balance_account.balance)).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                        balance_before_cents = int(balance_before * 100)

                        balance_cents_before = balance_account.balance_cents or 0
                        await db.execute(
                            update(UserBalance)
                            .where(UserBalance.user_id == order.user_id)
                            .values(
                                balance=balance_account.balance + float(refund_amount),
                                balance_cents=balance_cents_before + refund_amount_cents,
                            )
                        )

                        balance_after = balance_before + refund_amount
                        balance_after_cents = balance_before_cents + refund_amount_cents

                        # 创建余额交易记录
                        transaction = BalanceTransaction(
                            user_id=order.user_id,
                            order_id=order.id,
                            type="refund",
                            amount=float(refund_amount),
                            balance_before=float(balance_before),
                            balance_after=float(balance_after),
                            amount_cents=refund_amount_cents,
                            balance_before_cents=balance_before_cents,
                            balance_after_cents=balance_after_cents,
                            description=f"咨询超时自动取消退款: {order.title}",
                        )
                        db.add(transaction)

                        print(
                            f"  - 咨询 #{consultation.id}: 已退款 {refund_amount} 元到用户余额"
                        )
                    else:
                        # 非余额支付，标记为待退款
                        print(
                            f"  - 咨询 #{consultation.id}: 非余额支付，需要手动处理退款"
                        )

                # 更新咨询状态
                consultation.status = "cancelled"
                db.add(consultation)

                # 发送通知
                notification = Notification(
                    user_id=int(consultation.user_id),
                    type=NotificationType.SYSTEM,
                    title="咨询已超时取消",
                    content=f"您的咨询预约（{consultation.subject}）因超过{TIMEOUT_HOURS}小时未接单已自动取消。如有需要，请重新预约。",
                    link="/consultations",
                    is_read=False,
                )
                db.add(notification)

                print(f"  - 咨询 #{consultation.id}: 已取消并发送通知")

            except Exception as e:
                print(f"  - 咨询 #{consultation.id}: 处理失败 - {e}")
                await db.rollback()
                continue

        await db.commit()
        print(f"[{datetime.now(timezone.utc)}] 超时咨询处理完成")


async def main():
    """主函数"""
    print("=" * 60)
    print("咨询超时自动取消定时任务")
    print("=" * 60)

    try:
        await check_consultation_timeout()
    except Exception as e:
        print(f"执行失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    print("=" * 60)
    print("任务执行完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
