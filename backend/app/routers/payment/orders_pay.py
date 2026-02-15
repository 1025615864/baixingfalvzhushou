from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Integer, func, select, update
from sqlalchemy import cast as sa_cast
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...database import get_db
from ...models.payment import BalanceTransaction, PaymentOrder, PaymentStatus, UserBalance
from ...models.user import User
from ...services.prometheus_metrics import prometheus_metrics
from ...utils.deps import get_current_user

from . import crypto_utils as payment_crypto
from . import helpers as payment_helpers
from . import post_processing as payment_post

router = APIRouter()
settings = get_settings()
legacy = SimpleNamespace(
    PaymentOrder=PaymentOrder,
    UserBalance=UserBalance,
    BalanceTransaction=BalanceTransaction,
    PaymentStatus=PaymentStatus,
    select=select,
    update=update,
    func=func,
    sa_cast=sa_cast,
    Integer=Integer,
    settings=settings,
    _quantize_amount=payment_helpers._quantize_amount,
    _decimal_to_cents=payment_helpers._decimal_to_cents,
    generate_order_no=payment_helpers.generate_order_no,
    _get_or_create_balance_in_tx=payment_post._get_or_create_balance_in_tx,
    _maybe_apply_vip_membership_in_tx=payment_post._maybe_apply_vip_membership_in_tx,
    _maybe_apply_ai_pack_in_tx=payment_post._maybe_apply_ai_pack_in_tx,
    _maybe_confirm_lawyer_consultation_in_tx=payment_post._maybe_confirm_lawyer_consultation_in_tx,
    _maybe_create_consultation_review_task_in_tx=payment_post._maybe_create_consultation_review_task_in_tx,
    _append_query_param=payment_helpers._append_query_param,
    _ikunpay_build_submit_pay_url=payment_crypto.build_submit_pay_url,
    _alipay_build_page_pay_url=payment_crypto.build_page_pay_url,
)


class PayOrderRequest(BaseModel):
    payment_method: str


def _record(method: str, result: str) -> None:
    try:
        prometheus_metrics.record_payment_pay(
            method=str(method), result=str(result))
    except Exception:
        logger.exception("Failed to record payment metrics")
        return


def _as_str(value: object) -> str:
    return str(value or "").strip()


@router.post("/orders/{order_no}/pay", summary="支付订单")
async def pay_order(
    order_no: str,
    data: PayOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    method = _as_str(getattr(data, "payment_method", ""))
    out: dict[str, object] | None = None

    try:
        if data.payment_method not in {
                "alipay", "wechat", "balance", "ikunpay"}:
            raise HTTPException(status_code=400, detail="无效的支付方式")

        result = await db.execute(
            legacy.select(legacy.PaymentOrder).where(
                legacy.PaymentOrder.order_no == order_no,
                legacy.PaymentOrder.user_id == current_user.id,
            )
        )
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        if order.order_type == "recharge" and data.payment_method == "balance":
            raise HTTPException(status_code=400, detail="充值订单不支持余额支付")

        if order.status == legacy.PaymentStatus.PAID:
            out = {"message": "支付成功", "trade_no": order.trade_no}
        else:
            if order.status != legacy.PaymentStatus.PENDING:
                raise HTTPException(
                    status_code=400,
                    detail=f"订单状态异常: {order.status}")
        if out is None:
            expires_at = order.expires_at
            if expires_at is not None and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at and expires_at < datetime.now(timezone.utc):
                order.status = legacy.PaymentStatus.CANCELLED
                await db.commit()
                raise HTTPException(status_code=400, detail="订单已过期")

            actual_amount = legacy._quantize_amount(float(order.actual_amount))
            actual_amount_cents = legacy._decimal_to_cents(actual_amount)

            if data.payment_method == "wechat":
                raise HTTPException(status_code=400, detail="微信支付暂未开放")

            if data.payment_method == "balance":
                trade_no = f"BAL{legacy.generate_order_no()}"
                paid_at = datetime.now(timezone.utc)

                try:
                    balance_account = await legacy._get_or_create_balance_in_tx(db, current_user.id)
                    balance_before = legacy._quantize_amount(
                        float(balance_account.balance))
                    balance_before_cents = legacy._decimal_to_cents(
                        balance_before)

                    if balance_before < actual_amount:
                        raise HTTPException(status_code=400, detail="余额不足")

                    effective_balance_cents = legacy.func.coalesce(
                        legacy.UserBalance.balance_cents,
                        legacy.sa_cast(
                            legacy.func.round(
                                legacy.func.coalesce(
                                    legacy.UserBalance.balance,
                                    0) * 100),
                            legacy.Integer),
                    )
                    effective_total_consumed_cents = legacy.func.coalesce(
                        legacy.UserBalance.total_consumed_cents,
                        legacy.sa_cast(
                            legacy.func.round(
                                legacy.func.coalesce(
                                    legacy.UserBalance.total_consumed,
                                    0) * 100),
                            legacy.Integer,
                        ),
                    )

                    bal_update = await db.execute(
                        legacy.update(legacy.UserBalance)
                        .where(
                            legacy.UserBalance.user_id == current_user.id,
                            effective_balance_cents >= actual_amount_cents,
                        )
                        .values(
                            balance=legacy.func.coalesce(
                                legacy.UserBalance.balance, 0) - float(actual_amount),
                            total_consumed=legacy.func.coalesce(
                                legacy.UserBalance.total_consumed, 0) + float(actual_amount),
                            balance_cents=effective_balance_cents - actual_amount_cents,
                            total_consumed_cents=effective_total_consumed_cents + actual_amount_cents,
                        )
                    )
                    if getattr(bal_update, "rowcount", 0) != 1:
                        raise HTTPException(status_code=400, detail="余额不足")

                    order_update = await db.execute(
                        legacy.update(legacy.PaymentOrder)
                        .where(legacy.PaymentOrder.id == order.id, legacy.PaymentOrder.status == legacy.PaymentStatus.PENDING)
                        .values(
                            status=legacy.PaymentStatus.PAID,
                            payment_method=data.payment_method,
                            paid_at=paid_at,
                            trade_no=trade_no,
                            amount_cents=legacy.func.coalesce(
                                legacy.PaymentOrder.amount_cents,
                                legacy.sa_cast(
                                    legacy.func.round(
                                        legacy.PaymentOrder.amount * 100),
                                    legacy.Integer),
                            ),
                            actual_amount_cents=actual_amount_cents,
                        )
                    )
                    if getattr(order_update, "rowcount", 0) != 1:
                        raise HTTPException(status_code=400, detail="订单状态异常")

                    balance_after = balance_before - actual_amount
                    balance_after_cents = balance_before_cents - actual_amount_cents
                    transaction = legacy.BalanceTransaction(
                        user_id=current_user.id,
                        order_id=order.id,
                        type="consume",
                        amount=-float(actual_amount),
                        balance_before=float(balance_before),
                        balance_after=float(balance_after),
                        amount_cents=-actual_amount_cents,
                        balance_before_cents=balance_before_cents,
                        balance_after_cents=balance_after_cents,
                        description=f"支付订单: {order.title}",
                    )
                    db.add(transaction)

                    await legacy._maybe_apply_vip_membership_in_tx(db, order)
                    await legacy._maybe_apply_ai_pack_in_tx(db, order)
                    await legacy._maybe_confirm_lawyer_consultation_in_tx(db, order)
                    await legacy._maybe_create_consultation_review_task_in_tx(db, order)

                    await db.commit()
                except HTTPException:
                    await db.rollback()
                    raise
                except Exception:
                    logger.exception("Payment processing failed")
                    await db.rollback()
                    raise

                await db.refresh(order)
                out = {"message": "支付成功", "trade_no": order.trade_no}
            elif data.payment_method == "ikunpay":
                settings = legacy.settings
                if not (settings.ikunpay_pid or "").strip():
                    raise HTTPException(
                        status_code=400, detail="IKUNPAY_PID 未设置")
                if not (settings.ikunpay_key or "").strip():
                    raise HTTPException(
                        status_code=400, detail="IKUNPAY_KEY 未设置")
                if not (settings.ikunpay_notify_url or "").strip():
                    raise HTTPException(
                        status_code=400, detail="IKUNPAY_NOTIFY_URL 未设置")

                if order.payment_method != "ikunpay":
                    order.payment_method = "ikunpay"
                    db.add(order)
                    await db.commit()
                    await db.refresh(order)

                pay_type_raw = (settings.ikunpay_default_type or "").strip()
                pay_type = pay_type_raw or None
                return_url = (
                    settings.ikunpay_return_url or "").strip() or None
                if return_url is None:
                    frontend_base = str(
                        getattr(
                            settings,
                            "frontend_base_url",
                            "") or "").strip().rstrip("/")
                    if frontend_base:
                        return_url = f"{frontend_base}/payment/return"

                if return_url:
                    return_url = legacy._append_query_param(
                        return_url, "order_no", order.order_no)

                pay_url = legacy._ikunpay_build_submit_pay_url(
                    gateway_url=(settings.ikunpay_gateway_url or "").strip(
                    ) or "https://ikunpay.com/submit.php",
                    pid=settings.ikunpay_pid,
                    pay_type=pay_type,
                    out_trade_no=order.order_no,
                    notify_url=settings.ikunpay_notify_url,
                    return_url=return_url,
                    name=order.title,
                    money=legacy._quantize_amount(float(order.actual_amount)),
                    key=settings.ikunpay_key,
                )
                out = {
                    "message": "OK",
                    "payment_method": "ikunpay",
                    "amount": order.actual_amount,
                    "order_no": order.order_no,
                    "pay_url": pay_url,
                }
            elif data.payment_method == "alipay":
                settings = legacy.settings
                if not settings.alipay_app_id or not settings.alipay_private_key:
                    raise HTTPException(status_code=400, detail="支付宝配置未设置")
                if not settings.alipay_notify_url:
                    raise HTTPException(
                        status_code=400, detail="ALIPAY_NOTIFY_URL 未设置")

                if order.payment_method != "alipay":
                    order.payment_method = "alipay"
                    db.add(order)
                    await db.commit()
                    await db.refresh(order)

                return_url = (settings.alipay_return_url or "").strip() or None
                if return_url is None:
                    frontend_base = str(
                        getattr(
                            settings,
                            "frontend_base_url",
                            "") or "").strip().rstrip("/")
                    if frontend_base:
                        return_url = f"{frontend_base}/payment/return"

                if return_url:
                    return_url = legacy._append_query_param(
                        return_url, "order_no", order.order_no)

                pay_url = legacy._alipay_build_page_pay_url(
                    gateway_url=settings.alipay_gateway_url,
                    app_id=settings.alipay_app_id,
                    private_key=settings.alipay_private_key,
                    notify_url=settings.alipay_notify_url,
                    return_url=return_url,
                    out_trade_no=order.order_no,
                    total_amount=legacy._quantize_amount(
                        float(order.actual_amount)),
                    subject=order.title,
                )
                out = {
                    "message": "OK",
                    "payment_method": "alipay",
                    "amount": order.actual_amount,
                    "order_no": order.order_no,
                    "pay_url": pay_url,
                }
            else:
                out = {
                    "message": "请使用第三方支付",
                    "payment_method": data.payment_method,
                    "amount": order.actual_amount,
                    "order_no": order.order_no,
                }

        if out is None:
            out = {
                "message": "请使用第三方支付",
                "payment_method": data.payment_method}
    except HTTPException as e:
        detail = _as_str(getattr(e, "detail", ""))
        if detail == "无效的支付方式":
            _record(method, "invalid_method")
        elif detail == "订单不存在":
            _record(method, "order_not_found")
        elif detail == "订单已过期":
            _record(method, "expired")
        elif detail == "充值订单不支持余额支付":
            _record(method, "not_allowed")
        elif detail == "微信支付暂未开放":
            _record(method, "not_supported")
        elif detail.startswith("订单状态异常"):
            _record(method, "status_invalid")
        elif method in {"alipay", "ikunpay"} and (
            "未设置" in detail or "配置未设置" in detail
        ):
            _record(method, "config_missing")
        raise

    if method != "balance" and isinstance(
            out, dict) and _as_str(out.get("trade_no")):
        _record(method, "already_paid")
    else:
        _record(method, "ok")

    return out
