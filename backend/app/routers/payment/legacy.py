from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from urllib.parse import urlencode, quote

from fastapi import HTTPException
from sqlalchemy import select, update, func, cast, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.payment import PaymentOrder, PaymentStatus, UserBalance, BalanceTransaction
from app.models.user import User
from app.services.prometheus_metrics import prometheus_metrics

settings = get_settings()


def _get_settings():
    return get_settings()


def _quantize_amount(v: float) -> float:
    return round(float(v), 2)


def _decimal_to_cents(v: float) -> int:
    return int(round(float(v) * 100))


def generate_order_no() -> str:
    import uuid
    return uuid.uuid4().hex[:16].upper()


async def _get_or_create_balance_in_tx(db: AsyncSession, user_id: int):
    stmt = select(UserBalance).where(UserBalance.user_id == user_id)
    result = await db.execute(stmt)
    balance = result.scalar_one_or_none()
    if balance is None:
        balance = UserBalance(user_id=user_id, balance=0.0)
        db.add(balance)
        await db.flush()
    return balance


async def _maybe_apply_vip_membership_in_tx(db, order, user):
    pass


async def _maybe_apply_ai_pack_in_tx(db, order, user):
    pass


async def _maybe_confirm_lawyer_consultation_in_tx(db, order, user):
    pass


async def _maybe_create_consultation_review_task_in_tx(db, order, user):
    pass


def _append_query_param(url: str, key: str, value: str) -> str:
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{key}={value}"


def _ikunpay_build_submit_pay_url(**kwargs) -> str:
    return "https://ikunpay.cn/pay.php?" + urlencode(kwargs, quote_via=quote)


def _alipay_build_page_pay_url(**kwargs) -> str:
    return "https://openapi.alipay.com/gateway.do?" + urlencode(kwargs, quote_via=quote)


async def pay_order(
    order_no: str,
    data,
    current_user,
    db: AsyncSession,
):
    payment_method = getattr(data, "payment_method", "alipay")

    valid_methods = {"alipay", "wechat", "balance", "ikunpay"}
    if payment_method not in valid_methods:
        prometheus_metrics.record_payment_pay(method=payment_method, result="invalid_method")
        raise HTTPException(status_code=400, detail="不支持的支付方式")

    stmt = select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        prometheus_metrics.record_payment_pay(method=payment_method, result="order_not_found")
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status == PaymentStatus.PAID:
        prometheus_metrics.record_payment_pay(method=payment_method, result="already_paid")
        return {"trade_no": order.trade_no, "payment_method": order.payment_method}

    if order.status not in (PaymentStatus.PENDING,):
        exp = getattr(order, "expires_at", None)
        if exp:
            try:
                exp_dt = exp.replace(tzinfo=None) if hasattr(exp, "replace") else exp
                if exp_dt < datetime.now(timezone.utc).replace(tzinfo=None):
                    order.status = PaymentStatus.CANCELLED
                    await db.commit()
                    prometheus_metrics.record_payment_pay(method=payment_method, result="expired")
                    raise HTTPException(status_code=400, detail="订单已过期")
            except (AttributeError, TypeError):
                pass
        prometheus_metrics.record_payment_pay(method=payment_method, result="status_invalid")
        raise HTTPException(status_code=400, detail="订单状态不允许支付")

    exp = getattr(order, "expires_at", None)
    if exp:
        try:
            exp_dt = exp.replace(tzinfo=None) if hasattr(exp, "replace") else exp
            if exp_dt < datetime.now(timezone.utc).replace(tzinfo=None):
                order.status = PaymentStatus.CANCELLED
                await db.commit()
                prometheus_metrics.record_payment_pay(method=payment_method, result="expired")
                raise HTTPException(status_code=400, detail="订单已过期")
        except (AttributeError, TypeError):
            pass

    if payment_method == "balance":
        if order.order_type == "recharge":
            prometheus_metrics.record_payment_pay(method=payment_method, result="not_allowed")
            raise HTTPException(status_code=400, detail="充值订单不能使用余额支付")

        balance_obj = await _get_or_create_balance_in_tx(db, current_user.id)
        if balance_obj.balance < order.actual_amount:
            await db.rollback()
            prometheus_metrics.record_payment_pay(method=payment_method, result="insufficient_balance")
            raise HTTPException(status_code=400, detail="余额不足")

        new_balance = _quantize_amount(balance_obj.balance - order.actual_amount)
        new_consumed = _quantize_amount((getattr(balance_obj, "total_consumed", None) or 0) + order.actual_amount)

        balance_cents = _decimal_to_cents(getattr(balance_obj, "balance_cents", None) or 0) - _decimal_to_cents(getattr(order, "actual_amount_cents", None) or _decimal_to_cents(order.actual_amount))
        consumed_cents = _decimal_to_cents(getattr(balance_obj, "total_consumed_cents", None) or 0) + _decimal_to_cents(getattr(order, "actual_amount_cents", None) or _decimal_to_cents(order.actual_amount))

        stmt_upd = (
            update(UserBalance)
            .where(UserBalance.user_id == current_user.id, UserBalance.balance == balance_obj.balance)
            .values(
                balance=new_balance,
                total_consumed=new_consumed,
                balance_cents=balance_cents,
                total_consumed_cents=consumed_cents,
            )
        )
        result = await db.execute(stmt_upd)
        if result.rowcount == 0:
            await db.rollback()
            prometheus_metrics.record_payment_pay(method=payment_method, result="insufficient_balance")
            raise HTTPException(status_code=400, detail="余额扣减失败，请重试")

        order.status = PaymentStatus.PAID
        order.payment_method = "balance"
        order.paid_at = datetime.now(timezone.utc)
        if not order.trade_no:
            order.trade_no = "BAL" + generate_order_no()

        await _maybe_apply_vip_membership_in_tx(db, order, current_user)
        await _maybe_apply_ai_pack_in_tx(db, order, current_user)
        await _maybe_confirm_lawyer_consultation_in_tx(db, order, current_user)
        await _maybe_create_consultation_review_task_in_tx(db, order, current_user)

        db.add(BalanceTransaction(
            user_id=current_user.id,
            order_id=order.id,
            type="consume",
            amount=-order.actual_amount,
            balance_before=balance_obj.balance,
            balance_after=new_balance,
        ))

        await db.commit()
        await db.refresh(order)

        prometheus_metrics.record_payment_pay(method=payment_method, result="ok")
        return {"trade_no": order.trade_no, "payment_method": "balance"}

    if payment_method == "wechat":
        prometheus_metrics.record_payment_pay(method=payment_method, result="not_supported")
        raise HTTPException(status_code=400, detail="微信支付暂未接入")

    if payment_method == "ikunpay":
        s = _get_settings()
        pid = getattr(s, "ikunpay_pid", "") or ""
        key = getattr(s, "ikunpay_key", "") or ""
        notify_url = getattr(s, "ikunpay_notify_url", "") or ""
        if not pid or not key or not notify_url:
            prometheus_metrics.record_payment_pay(method=payment_method, result="config_missing")
            raise HTTPException(status_code=400, detail="支付配置缺失")

        return_url = getattr(s, "ikunpay_return_url", "") or ""
        if return_url:
            return_url = _append_query_param(return_url, "order_no", order_no)

        pay_url = _ikunpay_build_submit_pay_url(
            pid=pid, type="alipay", out_trade_no=order_no,
            notify_url=notify_url, return_url=return_url,
            name=order.title, money=f"{order.actual_amount:.2f}",
        )

        order.payment_method = "ikunpay"
        await db.commit()
        await db.refresh(order)

        prometheus_metrics.record_payment_pay(method=payment_method, result="ok")
        return {"pay_url": pay_url, "payment_method": "ikunpay"}

    if payment_method == "alipay":
        s = get_settings()
        app_id = getattr(s, "alipay_app_id", "") or ""
        private_key = getattr(s, "alipay_private_key", "") or ""
        notify_url = getattr(s, "alipay_notify_url", "") or ""
        if not app_id or not private_key or not notify_url:
            prometheus_metrics.record_payment_pay(method=payment_method, result="config_missing")
            raise HTTPException(status_code=400, detail="支付宝配置缺失")

        return_url = getattr(s, "alipay_return_url", "") or ""
        if return_url:
            return_url = _append_query_param(return_url, "order_no", order_no)

        pay_url = _alipay_build_page_pay_url(
            app_id=app_id, method="alipay.trade.page.pay",
            notify_url=notify_url, return_url=return_url,
        )

        order.payment_method = "alipay"
        await db.commit()
        await db.refresh(order)

        prometheus_metrics.record_payment_pay(method=payment_method, result="ok")
        return {"pay_url": pay_url, "payment_method": "alipay"}

    prometheus_metrics.record_payment_pay(method=payment_method, result="invalid_method")
    raise HTTPException(status_code=400, detail="不支持的支付方式")
