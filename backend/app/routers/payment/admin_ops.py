from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import Integer, cast as sa_cast, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from ...database import get_db
from ...models.payment import BalanceTransaction, PaymentCallbackEvent, PaymentOrder, PaymentStatus, UserBalance
from ...models.user import User
from ...utils.deps import require_admin
from . import crypto_utils as payment_crypto
from . import helpers as payment_helpers
from . import post_processing as payment_post
router = APIRouter()


class MarkPaidRequest(BaseModel):
    payment_method: str


class ReconcileEventItem(BaseModel):
    provider: str
    order_no: str | None
    trade_no: str | None
    amount: float | None
    verified: bool
    error_message: str | None
    created_at: datetime


class ReconcileResponse(BaseModel):
    order_no: str
    order_status: str
    payment_method: str | None
    actual_amount: float
    trade_no: str | None
    callbacks_total: int
    callbacks_verified: int
    callbacks_failed: int
    diagnosis: str
    details: dict[str, object]
    paid_at: datetime | None
    recent_events: list[ReconcileEventItem]


class CallbackEventResponse(BaseModel):
    id: int
    provider: str
    order_no: str | None
    trade_no: str | None
    amount: float | None
    verified: bool
    error_message: str | None
    created_at: datetime


class CallbackEventDetailResponse(CallbackEventResponse):
    raw_payload: str | None
    masked_payload: str | None
    raw_payload_hash: str | None
    source_ip: str | None
    user_agent: str | None


@router.get("/admin/orders", summary="管理员-订单列表")
async def admin_get_orders(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: str | None = None,
    user_id: int | None = None,
):
    """管理员获取所有订单"""
    _ = current_user
    query = select(
        PaymentOrder,
        User.username).join(
        User,
        User.id == PaymentOrder.user_id)

    if status_filter:
        query = query.where(PaymentOrder.status == status_filter)
    if user_id:
        query = query.where(PaymentOrder.user_id == user_id)

    count_query = select(func.count()).select_from(query.subquery())
    total: int = int(await db.scalar(count_query) or 0)

    query = query.order_by(PaymentOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = cast(list[tuple[PaymentOrder, str]], result.all())

    items: list[dict[str, object]] = []
    for o, username in rows:
        items.append(
            {
                "id": o.id,
                "order_no": o.order_no,
                "user_id": o.user_id,
                "username": username,
                "order_type": o.order_type,
                "amount": o.amount,
                "actual_amount": o.actual_amount,
                "status": o.status,
                "payment_method": o.payment_method,
                "title": o.title,
                "created_at": o.created_at,
                "paid_at": o.paid_at,
            }
        )

    return {"items": items, "total": total}


@router.post("/admin/refund/{order_no}", summary="管理员-退款")
async def admin_refund(
    order_no: str,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """管理员退款"""
    _ = current_user
    result = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == order_no))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status == PaymentStatus.REFUNDED:
        return {"message": "退款成功"}

    if order.status != PaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="只能退款已支付订单")

    refund_amount = payment_helpers._quantize_amount(
        float(order.actual_amount))
    refund_amount_cents = payment_helpers._decimal_to_cents(refund_amount)

    try:
        order_update = await db.execute(
            update(PaymentOrder)
            .where(PaymentOrder.id == order.id, PaymentOrder.status == PaymentStatus.PAID)
            .values(status=PaymentStatus.REFUNDED)
        )
        if getattr(order_update, "rowcount", 0) != 1:
            raise HTTPException(status_code=400, detail="订单状态异常")

        if order.payment_method == "balance":
            balance_account = await payment_post._get_or_create_balance_in_tx(db, order.user_id)
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

            _ = await db.execute(
                update(UserBalance)
                .where(UserBalance.user_id == order.user_id)
                .values(
                    balance=func.coalesce(
                        UserBalance.balance, 0) + float(refund_amount),
                    balance_cents=effective_balance_cents + refund_amount_cents,
                )
            )

            balance_after = balance_before + refund_amount
            balance_after_cents = balance_before_cents + refund_amount_cents
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
                description=f"退款: {order.title}",
            )
            db.add(transaction)

        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        logger.exception("Refund failed")
        await db.rollback()
        raise

    return {"message": "退款成功"}


@router.post("/admin/orders/{order_no}/mark-paid", summary="管理员-标记订单已支付")
async def admin_mark_paid(
    order_no: str,
    data: MarkPaidRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """管理员标记订单已支付（开发环境/人工对账用）"""
    _ = current_user

    if data.payment_method not in {"alipay", "wechat"}:
        raise HTTPException(status_code=400, detail="无效的支付方式")

    result = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == order_no))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status == PaymentStatus.PAID:
        return {"message": "订单已是支付成功状态"}

    if order.status != PaymentStatus.PENDING:
        raise HTTPException(status_code=400, detail="订单状态异常")

    if order.order_type != "recharge":
        raise HTTPException(status_code=400, detail="仅充值订单支持该操作")

    paid_at = datetime.now(timezone.utc)
    trade_no = f"ADM{payment_helpers.generate_order_no()}"
    recharge_amount = payment_helpers._quantize_amount(
        float(order.actual_amount))
    recharge_amount_cents = payment_helpers._decimal_to_cents(recharge_amount)

    try:
        order_update = await db.execute(
            update(PaymentOrder)
            .where(PaymentOrder.id == order.id, PaymentOrder.status == PaymentStatus.PENDING)
            .values(
                status=PaymentStatus.PAID,
                payment_method=data.payment_method,
                paid_at=paid_at,
                trade_no=trade_no,
                amount_cents=func.coalesce(
                    PaymentOrder.amount_cents,
                    sa_cast(func.round(PaymentOrder.amount * 100), Integer),
                ),
                actual_amount_cents=recharge_amount_cents,
            )
        )
        if getattr(order_update, "rowcount", 0) != 1:
            raise HTTPException(status_code=400, detail="订单状态异常")

        balance_account = await payment_post._get_or_create_balance_in_tx(db, order.user_id)
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
                balance=func.coalesce(
                    UserBalance.balance,
                    0) + float(recharge_amount),
                total_recharged=func.coalesce(
                    UserBalance.total_recharged,
                    0) + float(recharge_amount),
                balance_cents=effective_balance_cents + recharge_amount_cents,
                total_recharged_cents=effective_total_recharged_cents + recharge_amount_cents,
            )
        )

        balance_after = balance_before + recharge_amount
        balance_after_cents = balance_before_cents + recharge_amount_cents
        transaction = BalanceTransaction(
            user_id=order.user_id,
            order_id=order.id,
            type="recharge",
            amount=float(recharge_amount),
            balance_before=float(balance_before),
            balance_after=float(balance_after),
            amount_cents=recharge_amount_cents,
            balance_before_cents=balance_before_cents,
            balance_after_cents=balance_after_cents,
            description=f"充值: {order.title}",
        )
        db.add(transaction)

        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        logger.exception("Mark paid failed")
        await db.rollback()
        raise

    return {"message": "标记成功"}


@router.get("/admin/callback-events", summary="管理员-支付回调事件")
async def admin_callback_events(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    provider: str | None = None,
    order_no: str | None = None,
    trade_no: str | None = None,
    verified: bool | None = None,
    q: str | None = None,
    has_error: bool | None = None,
    from_ts: int | None = None,
    to_ts: int | None = None,
):
    _ = current_user
    query = select(PaymentCallbackEvent)

    if provider:
        query = query.where(PaymentCallbackEvent.provider == provider)
    if order_no:
        query = query.where(PaymentCallbackEvent.order_no == order_no)
    if trade_no:
        query = query.where(PaymentCallbackEvent.trade_no == trade_no)
    if verified is not None:
        query = query.where(PaymentCallbackEvent.verified == bool(verified))

    if q and str(q).strip():
        kw = f"%{str(q).strip()}%"
        query = query.where(
            (
                PaymentCallbackEvent.order_no.ilike(kw)
                | PaymentCallbackEvent.trade_no.ilike(kw)
                | PaymentCallbackEvent.error_message.ilike(kw)
            )
        )

    if has_error is not None:
        if bool(has_error):
            query = query.where(
                PaymentCallbackEvent.error_message.is_not(None)
                & (PaymentCallbackEvent.error_message != "")
            )
        else:
            query = query.where(
                (PaymentCallbackEvent.error_message.is_(None))
                | (PaymentCallbackEvent.error_message == "")
            )

    if from_ts is not None:
        try:
            dt = datetime.fromtimestamp(
                int(from_ts),
                tz=timezone.utc).replace(
                tzinfo=None)
            query = query.where(PaymentCallbackEvent.created_at >= dt)
        except Exception:
            pass

    if to_ts is not None:
        try:
            dt = datetime.fromtimestamp(
                int(to_ts), tz=timezone.utc).replace(
                tzinfo=None)
            query = query.where(PaymentCallbackEvent.created_at <= dt)
        except Exception:
            pass

    count_query = select(func.count()).select_from(query.subquery())
    total: int = int(await db.scalar(count_query) or 0)

    query = query.order_by(PaymentCallbackEvent.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(query)
    events = res.scalars().all()

    items = [
        CallbackEventResponse(
            id=e.id,
            provider=e.provider,
            order_no=e.order_no,
            trade_no=e.trade_no,
            amount=e.amount,
            verified=bool(e.verified),
            error_message=e.error_message,
            created_at=e.created_at,
        )
        for e in events
    ]
    return {"items": items, "total": total}


@router.get("/admin/callback-events/stats", summary="管理员-支付回调统计")
async def admin_callback_event_stats(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    minutes: Annotated[int, Query(ge=1, le=60 * 24 * 30)] = 60,
    provider: str | None = None,
):
    _ = current_user
    now = datetime.now(timezone.utc)
    since = now - timedelta(minutes=int(minutes))
    since_naive = since.replace(tzinfo=None)

    base_where: list[ColumnElement[bool]] = []
    if provider:
        base_where.append(PaymentCallbackEvent.provider == provider)

    all_total = await db.scalar(select(func.count()).select_from(PaymentCallbackEvent).where(*base_where)) or 0
    all_verified = await db.scalar(
        select(func.count()).select_from(PaymentCallbackEvent).where(
            *base_where, PaymentCallbackEvent.verified
        )
    ) or 0
    all_failed = int(all_total) - int(all_verified)

    window_where: list[ColumnElement[bool]] = [
        *base_where,
        PaymentCallbackEvent.created_at >= since_naive,
    ]
    window_total = await db.scalar(select(func.count()).select_from(PaymentCallbackEvent).where(*window_where)) or 0
    window_verified = await db.scalar(
        select(func.count()).select_from(PaymentCallbackEvent).where(
            *window_where, PaymentCallbackEvent.verified
        )
    ) or 0
    window_failed = int(window_total) - int(window_verified)

    return {
        "minutes": int(minutes),
        "provider": provider,
        "all_total": int(all_total),
        "all_verified": int(all_verified),
        "all_failed": int(all_failed),
        "window_total": int(window_total),
        "window_verified": int(window_verified),
        "window_failed": int(window_failed),
    }


@router.get(
    "/admin/callback-events/{event_id}",
    response_model=CallbackEventDetailResponse,
    summary="管理员-支付回调事件详情",
)
async def admin_callback_event_detail(
    event_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user
    res = await db.execute(select(PaymentCallbackEvent).where(PaymentCallbackEvent.id == int(event_id)))
    e = res.scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="回调事件不存在")

    return CallbackEventDetailResponse(
        id=e.id,
        provider=e.provider,
        order_no=e.order_no,
        trade_no=e.trade_no,
        amount=e.amount,
        verified=bool(e.verified),
        error_message=e.error_message,
        created_at=e.created_at,
        raw_payload=e.raw_payload,
        masked_payload=payment_crypto.mask_payload(e.raw_payload),
        raw_payload_hash=getattr(e, "raw_payload_hash", None),
        source_ip=getattr(e, "source_ip", None),
        user_agent=getattr(e, "user_agent", None),
    )


@router.post("/admin/callback-events/{event_id}/retry", summary="管理员-重试支付回调")
async def admin_retry_callback(
    event_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """手动重试支付回调处理"""
    _ = current_user
    
    # 获取回调事件
    res = await db.execute(select(PaymentCallbackEvent).where(PaymentCallbackEvent.id == int(event_id)))
    event = res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="回调事件不存在")
    
    if not event.order_no:
        raise HTTPException(status_code=400, detail="回调事件没有关联订单号")
    
    # 获取对应订单
    order_res = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == event.order_no))
    order = order_res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="关联订单不存在")
    
    # 如果订单已支付，返回成功
    if order.status == PaymentStatus.PAID:
        return {"message": "订单已支付，无需处理", "success": True}
    
    try:
        # 重新处理回调
        # 这里调用原有的回调处理逻辑
        from .callback import process_payment_callback
        
        result = await process_payment_callback(
            db=db,
            provider=event.provider,
            payload=event.raw_payload,
            source_ip=getattr(event, "source_ip", None),
            user_agent=getattr(event, "user_agent", None),
        )
        
        await db.commit()
        return {"message": "回调重试成功", "success": True, "result": result}
    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"回调重试失败: {str(e)}")


class ProcessCallbackRequest(BaseModel):
    success: bool
    note: str | None = None


@router.post("/admin/callback-events/{event_id}/process", summary="管理员-手动处理支付回调")
async def admin_process_callback(
    event_id: int,
    data: ProcessCallbackRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """手动标记回调处理结果"""
    _ = current_user
    
    # 获取回调事件
    res = await db.execute(select(PaymentCallbackEvent).where(PaymentCallbackEvent.id == int(event_id)))
    event = res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="回调事件不存在")
    
    if not event.order_no:
        raise HTTPException(status_code=400, detail="回调事件没有关联订单号")
    
    # 获取对应订单
    order_res = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == event.order_no))
    order = order_res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="关联订单不存在")
    
    try:
        if data.success:
            # 标记为成功 - 更新订单状态为已支付
            if order.status != PaymentStatus.PAID:
                # 更新订单状态
                await db.execute(
                    update(PaymentOrder)
                    .where(PaymentOrder.id == order.id)
                    .values(
                        status=PaymentStatus.PAID,
                        payment_method=event.provider,
                        paid_at=datetime.now(timezone.utc),
                        trade_no=event.trade_no or f"MANUAL{payment_helpers.generate_order_no()}",
                    )
                )
                
                # 如果是充值订单，更新用户余额
                if order.order_type == "recharge":
                    await payment_post._process_recharge_balance(db, order)
            
            # 更新回调事件状态
            event.verified = True
            event.error_message = f"手动标记成功 - {current_user.username}"
            if data.note:
                event.error_message += f": {data.note}"
        else:
            # 标记为失败
            event.verified = False
            event.error_message = f"手动标记失败 - {current_user.username}"
            if data.note:
                event.error_message += f": {data.note}"
        
        db.add(event)
        await db.commit()
        
        return {
            "message": "处理成功",
            "success": data.success,
            "order_no": event.order_no,
        }
    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/admin/reconcile/{order_no}", summary="管理员-订单与回调对账")
async def admin_reconcile_order(
    order_no: str,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
):
    _ = current_user
    res = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == order_no))
    order = res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    ev_res = await db.execute(
        select(PaymentCallbackEvent)
        .where(PaymentCallbackEvent.order_no == order_no)
        .order_by(PaymentCallbackEvent.created_at.desc())
        .limit(limit)
    )
    events = ev_res.scalars().all()

    recent_events = [
        ReconcileEventItem(
            provider=e.provider,
            order_no=e.order_no,
            trade_no=e.trade_no,
            amount=e.amount,
            verified=bool(e.verified),
            error_message=e.error_message,
            created_at=e.created_at,
        )
        for e in events
    ]

    callbacks_total = len(events)
    callbacks_verified = sum(1 for e in events if bool(e.verified))
    callbacks_failed = callbacks_total - callbacks_verified

    last_event = events[0] if events else None
    expected_amount = payment_helpers._quantize_amount(
        float(order.actual_amount))
    expected_amount_float = float(expected_amount)

    diagnosis = "ok"
    details: dict[str, object] = {
        "expected_amount": expected_amount_float,
        "last_event": {
            "provider": getattr(last_event, "provider", None),
            "verified": getattr(last_event, "verified", None),
            "error_message": getattr(last_event, "error_message", None),
            "created_at": getattr(last_event, "created_at", None),
        }
        if last_event
        else None,
    }

    if callbacks_total == 0:
        diagnosis = "no_callback"
    else:
        has_unverified = any(not bool(e.verified) for e in events)
        has_amount_mismatch = any(
            str(getattr(e, "error_message", "") or "") == "金额不一致" for e in events)
        has_decrypt_failed = any(
            str(getattr(e, "error_message", "") or "") == "解密失败" for e in events)
        has_sig_failed = any(
            str(getattr(e, "error_message", "") or "") == "验签失败" for e in events)
        has_verified_success = any(
            bool(
                e.verified) and not (
                getattr(
                    e,
                    "error_message",
                    None)) for e in events)

        if has_amount_mismatch:
            diagnosis = "amount_mismatch"
        elif has_decrypt_failed:
            diagnosis = "decrypt_failed"
        elif has_sig_failed or has_unverified:
            diagnosis = "signature_failed"
        elif str(order.status) == PaymentStatus.PAID and not has_verified_success:
            diagnosis = "paid_without_success_callback"
        elif str(order.status) != PaymentStatus.PAID and has_verified_success:
            diagnosis = "success_callback_but_order_not_paid"

        details.update(
            {
                "has_verified_success": has_verified_success,
                "has_unverified": has_unverified,
                "has_amount_mismatch": has_amount_mismatch,
                "has_decrypt_failed": has_decrypt_failed,
                "has_sig_failed": has_sig_failed,
            }
        )

    return ReconcileResponse(
        order_no=order.order_no,
        order_status=str(order.status),
        payment_method=order.payment_method,
        actual_amount=float(order.actual_amount),
        trade_no=order.trade_no,
        callbacks_total=int(callbacks_total),
        callbacks_verified=int(callbacks_verified),
        callbacks_failed=int(callbacks_failed),
        diagnosis=str(diagnosis),
        details=details,
        paid_at=order.paid_at,
        recent_events=recent_events,
    )
