from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import cast

from sqlalchemy import Integer, cast as sa_cast, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

logger = logging.getLogger(__name__)

from ...models.consultation import Consultation
from ...models.consultation_review import ConsultationReviewTask
from ...models.lawfirm import LawyerConsultation
from ...models.payment import BalanceTransaction, PaymentOrder, PaymentStatus, UserBalance
from ...models.notification import Notification, NotificationType
from ...models.user import User
from ...models.user_quota import UserQuotaPackBalance
from . import helpers as payment_helpers


async def _maybe_confirm_lawyer_consultation_in_tx(
        db: AsyncSession, order: PaymentOrder) -> None:
    if getattr(order, "related_type", None) != "lawyer_consultation":
        return

    related_id_raw: object | None = cast(
        object | None, getattr(
            order, "related_id", None))
    if related_id_raw is None:
        return

    related_id: int
    if isinstance(related_id_raw, bool):
        return
    if isinstance(related_id_raw, int):
        related_id = related_id_raw
    elif isinstance(related_id_raw, float):
        related_id = int(related_id_raw)
    elif isinstance(related_id_raw, str) and related_id_raw.strip():
        try:
            related_id = int(related_id_raw.strip())
        except Exception:
            logger.exception("Failed to parse related_id in consultation confirmation")
            return
    else:
        return

    _ = await db.execute(
        update(LawyerConsultation)
        .where(
            LawyerConsultation.id == related_id,
            LawyerConsultation.user_id == int(order.user_id),
            LawyerConsultation.status == "pending",
        )
        .values(
            status="confirmed",
            updated_at=func.now(),
        )
    )


async def _maybe_create_consultation_review_task_in_tx(
        db: AsyncSession, order: PaymentOrder) -> None:
    if str(getattr(order, "order_type", "")
           or "").lower() != "light_consult_review":
        return

    related_type = str(
        getattr(
            order,
            "related_type",
            "") or "").strip().lower()
    if related_type != "ai_consultation":
        return

    related_id_raw: object | None = cast(
        object | None, getattr(
            order, "related_id", None))
    related_id: int | None = None
    if isinstance(related_id_raw, bool) or related_id_raw is None:
        related_id = None
    elif isinstance(related_id_raw, int):
        related_id = related_id_raw
    elif isinstance(related_id_raw, float):
        related_id = int(related_id_raw)
    elif isinstance(related_id_raw, str) and related_id_raw.strip():
        try:
            related_id = int(related_id_raw.strip())
        except Exception:
            logger.exception("Failed to parse related_id in review task creation")
            related_id = None

    if related_id is None or related_id <= 0:
        return

    c_res = await db.execute(select(Consultation).where(Consultation.id == int(related_id)))
    c = c_res.scalar_one_or_none()
    if c is None:
        return
    if int(getattr(c, "user_id", 0) or 0) != int(order.user_id):
        return

    existing_res = await db.execute(
        select(ConsultationReviewTask).where(
            ConsultationReviewTask.order_id == int(order.id))
    )
    existing = existing_res.scalar_one_or_none()
    if existing is not None:
        return

    task = ConsultationReviewTask(
        consultation_id=int(related_id),
        user_id=int(order.user_id),
        order_id=int(order.id),
        order_no=str(order.order_no),
        status="pending",
    )
    db.add(task)


async def _maybe_apply_vip_membership_in_tx(
        db: AsyncSession, order: PaymentOrder) -> None:
    if str(getattr(order, "order_type", "")).lower() != "vip":
        return

    now = datetime.now(timezone.utc)
    res = await db.execute(select(User.vip_expires_at).where(User.id == int(order.user_id)))
    current = res.scalar_one_or_none()

    if isinstance(current, datetime) and current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    base = current if isinstance(current, datetime) and current > now else now
    vip_days, _vip_price = await payment_helpers._get_vip_plan(db)
    new_expires_at = base + timedelta(days=int(vip_days))

    _ = await db.execute(
        update(User)
        .where(User.id == int(order.user_id))
        .values(vip_expires_at=new_expires_at)
    )


async def _maybe_apply_ai_pack_in_tx(
        db: AsyncSession, order: PaymentOrder) -> None:
    if str(getattr(order, "order_type", "")).lower() != "ai_pack":
        return

    related_type = str(getattr(order, "related_type", "")
                       or "").strip().lower() or "ai_chat"
    if related_type not in payment_helpers.AI_PACK_RELATED_TYPES:
        return

    related_id_raw: object | None = cast(
        object | None, getattr(
            order, "related_id", None))
    if related_id_raw is None:
        return

    pack_count: int
    if isinstance(related_id_raw, bool):
        return
    if isinstance(related_id_raw, int):
        pack_count = related_id_raw
    elif isinstance(related_id_raw, float):
        pack_count = int(related_id_raw)
    elif isinstance(related_id_raw, str) and related_id_raw.strip():
        try:
            pack_count = int(related_id_raw.strip())
        except Exception:
            logger.exception("Failed to parse pack_count in AI pack application")
            return
    else:
        return

    options = await payment_helpers._get_pack_options(db, related_type)
    if pack_count not in options:
        return

    res = await db.execute(
        select(UserQuotaPackBalance).where(
            UserQuotaPackBalance.user_id == int(
                order.user_id))
    )
    row = res.scalar_one_or_none()
    if row is None:
        row = UserQuotaPackBalance(
            user_id=int(order.user_id),
            ai_chat_credits=0,
            document_generate_credits=0,
        )
        db.add(row)
        try:
            await db.flush()
        except Exception:
            await db.rollback()
            logger.exception("Failed to flush UserQuotaPackBalance")
            return

    if related_type == "document_generate":
        current = int(getattr(row, "document_generate_credits", 0))
        row.document_generate_credits = current + int(pack_count)
    else:
        current = int(getattr(row, "ai_chat_credits", 0))
        row.ai_chat_credits = current + int(pack_count)
    db.add(row)


async def _maybe_notify_payment_success_in_tx(
    db: AsyncSession,
    *,
    order: PaymentOrder,
    amount: Decimal,
) -> None:
    user_id = int(getattr(order, "user_id", 0) or 0)
    if user_id <= 0:
        return

    order_no = str(getattr(order, "order_no", "") or "").strip()
    if not order_no:
        return

    title = "支付成功"
    order_title = str(getattr(order, "title", "") or "").strip()
    amount_str = str(amount)
    content_lines = [
        f"订单：{order_title}" if order_title else "",
        f"订单号：{order_no}",
        f"实付金额：¥{amount_str}",
    ]
    content = "\n".join(line for line in content_lines if line)
    dedupe_key = f"payment_success:{order_no}"

    values = {
        "user_id": user_id,
        "type": NotificationType.SYSTEM,
        "title": title,
        "content": content or None,
        "link": "/orders?tab=payment",
        "dedupe_key": dedupe_key,
        "is_read": False,
    }

    bind = db.get_bind()
    dialect_name = str(
        getattr(
            getattr(
                bind,
                "dialect",
                None),
            "name",
            "") or "")
    if dialect_name == "postgresql":
        stmt = pg_insert(Notification).values(values).on_conflict_do_nothing(
            index_elements=["user_id", "type", "dedupe_key"]
        )
    else:
        stmt = sqlite_insert(Notification).values(values).on_conflict_do_nothing(
            index_elements=["user_id", "type", "dedupe_key"])

    await db.execute(stmt)

    try:
        from ...services.unified_notification_service import unified_notification_service

        existing = await unified_notification_service.get_existing_by_dedupe(
            db,
            user_id=user_id,
            notification_type=NotificationType.SYSTEM,
            dedupe_key=dedupe_key,
        )
        if existing is not None:
            await unified_notification_service.notify_ws(
                user_id=user_id,
                title=title,
                content=content,
                link=str(values.get("link") or ""),
                dedupe_key=dedupe_key,
                notification_id=int(existing.id),
            )
    except Exception:
        logger.exception("Failed to send payment success notification")


async def _mark_order_paid_in_tx(
    db: AsyncSession,
    *,
    order: PaymentOrder,
    payment_method: str,
    trade_no: str,
    amount: Decimal,
) -> bool:
    amount = payment_helpers._quantize_amount(float(amount))
    amount_cents = payment_helpers._decimal_to_cents(amount)
    paid_at = datetime.now(timezone.utc)

    order_update = await db.execute(
        update(PaymentOrder)
        .where(PaymentOrder.id == order.id, PaymentOrder.status == PaymentStatus.PENDING)
        .values(
            status=PaymentStatus.PAID,
            payment_method=payment_method,
            paid_at=paid_at,
            trade_no=trade_no,
            amount_cents=func.coalesce(
                PaymentOrder.amount_cents,
                sa_cast(func.round(PaymentOrder.amount * 100), Integer),
            ),
            actual_amount_cents=amount_cents,
        )
    )
    if getattr(order_update, "rowcount", 0) != 1:
        return False

    if order.order_type == "recharge":
        balance_account = await _get_or_create_balance_in_tx(db, order.user_id)
        balance_before = payment_helpers._quantize_amount(
            float(balance_account.balance))
        balance_before_cents = payment_helpers._decimal_to_cents(
            balance_before)

        effective_balance_cents = func.coalesce(
            UserBalance.balance_cents,
            sa_cast(
                func.round(
                    func.coalesce(
                        UserBalance.balance,
                        0) * 100),
                Integer),
        )
        effective_total_recharged_cents = func.coalesce(
            UserBalance.total_recharged_cents,
            sa_cast(
                func.round(
                    func.coalesce(
                        UserBalance.total_recharged,
                        0) * 100),
                Integer),
        )

        _ = await db.execute(
            update(UserBalance)
            .where(UserBalance.user_id == order.user_id)
            .values(
                balance=func.coalesce(UserBalance.balance, 0) + float(amount),
                total_recharged=func.coalesce(
                    UserBalance.total_recharged, 0) + float(amount),
                balance_cents=effective_balance_cents + amount_cents,
                total_recharged_cents=effective_total_recharged_cents + amount_cents,
            )
        )

        balance_after = balance_before + amount
        balance_after_cents = balance_before_cents + amount_cents
        transaction = BalanceTransaction(
            user_id=order.user_id,
            order_id=order.id,
            type="recharge",
            amount=float(amount),
            balance_before=float(balance_before),
            balance_after=float(balance_after),
            amount_cents=amount_cents,
            balance_before_cents=balance_before_cents,
            balance_after_cents=balance_after_cents,
            description=f"充值: {order.title}",
        )
        db.add(transaction)

    await _maybe_apply_vip_membership_in_tx(db, order)
    await _maybe_apply_ai_pack_in_tx(db, order)
    await _maybe_confirm_lawyer_consultation_in_tx(db, order)
    await _maybe_create_consultation_review_task_in_tx(db, order)
    await _maybe_notify_payment_success_in_tx(db, order=order, amount=amount)
    return True


async def _safe_post_processing(
    db: AsyncSession,
    order: PaymentOrder,
    amount: Decimal,
) -> None:
    """安全地执行支付后处理，捕获所有异常避免影响主流程"""
    post_processors = [
        _maybe_apply_vip_membership_in_tx,
        _maybe_apply_ai_pack_in_tx,
        _maybe_confirm_lawyer_consultation_in_tx,
        _maybe_create_consultation_review_task_in_tx,
        _maybe_notify_payment_success_in_tx,
    ]

    for processor in post_processors:
        try:
            if processor == _maybe_notify_payment_success_in_tx:
                await processor(db, order=order, amount=amount)
            else:
                await processor(db, order)
        except Exception:
            logger.exception(f"Payment post-processing failed in {processor.__name__}")


async def _get_or_create_balance_in_tx(
        db: AsyncSession, user_id: int) -> UserBalance:
    result = await db.execute(select(UserBalance).where(UserBalance.user_id == user_id))
    balance = result.scalar_one_or_none()
    if balance:
        return balance

    balance = UserBalance(
        user_id=user_id,
        balance=0.0,
        frozen=0.0,
        total_recharged=0.0,
        total_consumed=0.0,
        balance_cents=0,
        frozen_cents=0,
        total_recharged_cents=0,
        total_consumed_cents=0,
    )
    db.add(balance)
    await db.flush()
    return balance


async def get_or_create_balance(db: AsyncSession, user_id: int) -> UserBalance:
    """获取或创建用户余额账户"""
    result = await db.execute(select(UserBalance).where(UserBalance.user_id == user_id))
    balance = result.scalar_one_or_none()

    if not balance:
        balance = UserBalance(
            user_id=user_id,
            balance=0.0,
            frozen=0.0,
            total_recharged=0.0,
            total_consumed=0.0,
            balance_cents=0,
            frozen_cents=0,
            total_recharged_cents=0,
            total_consumed_cents=0,
        )
        db.add(balance)
        await db.commit()
        await db.refresh(balance)

    return balance
