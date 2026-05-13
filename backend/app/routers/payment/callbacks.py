from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.models.payment import PaymentOrder, PaymentStatus, PaymentCallbackEvent
from app.services.payment_service import payment_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def _record_callback_event(db: AsyncSession, provider: str, order_no: str, trade_no: str | None, amount: float | None, verified: bool, error_message: str | None, raw_payload: str, source_ip: str | None = None):
    event = PaymentCallbackEvent(
        provider=provider,
        order_no=order_no,
        trade_no=trade_no,
        amount=amount,
        verified=verified,
        error_message=error_message,
        raw_payload=raw_payload,
        source_ip=source_ip,
    )
    db.add(event)
    await db.commit()


@router.post("/callback/alipay/notify")
async def alipay_notify(request: Request, db: AsyncSession = Depends(get_db)):
    from app.routers.payment.crypto_utils import _alipay_verify_rsa2

    form_data = await request.form()
    params = dict(form_data)
    raw_payload = str(params)

    sign = params.get("sign", "")
    settings = get_settings()
    public_key = getattr(settings, "alipay_public_key", "") or ""

    order_no = params.get("out_trade_no", "")
    trade_no = params.get("trade_no", "")
    trade_status = params.get("trade_status", "")
    total_amount = params.get("total_amount", "0")

    try:
        amount = float(total_amount)
    except (ValueError, TypeError):
        amount = 0.0

    verified = False
    if public_key and sign:
        try:
            verified = _alipay_verify_rsa2(params, public_key, sign)
        except Exception as e:
            logger.warning(f"Alipay signature verification failed: {e}")

    if not verified and sign:
        await _record_callback_event(db, "alipay", order_no, trade_no, amount, False, "签名验证失败", raw_payload)
        return PlainTextResponse(content="failure", status_code=400)

    if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        await _record_callback_event(db, "alipay", order_no, trade_no, amount, verified, f"trade_status={trade_status}", raw_payload)
        return PlainTextResponse(content="success")

    try:
        order = await payment_service.mark_order_paid(db, order_no=order_no, payment_method="alipay", trade_no=trade_no)
        await _record_callback_event(db, "alipay", order_no, trade_no, amount, verified, None, raw_payload)
    except ValueError as e:
        await _record_callback_event(db, "alipay", order_no, trade_no, amount, verified, str(e), raw_payload)

    return PlainTextResponse(content="success")


@router.post("/callback/ikunpay/notify")
async def ikunpay_notify(request: Request, db: AsyncSession = Depends(get_db)):
    from app.routers.payment.crypto_utils import _ikunpay_verify_md5

    form_data = await request.form()
    params = dict(form_data)
    raw_payload = str(params)

    sign = params.get("sign", "")
    settings = get_settings()
    key = getattr(settings, "ikunpay_key", "") or ""

    order_no = params.get("out_trade_no", "")
    trade_no = params.get("trade_no", "")
    trade_status = params.get("trade_status", "")
    money = params.get("money", "0")

    try:
        amount = float(money)
    except (ValueError, TypeError):
        amount = 0.0

    verified = False
    if key and sign:
        verified = _ikunpay_verify_md5(params, key, sign)

    if not verified and sign:
        await _record_callback_event(db, "ikunpay", order_no, trade_no, amount, False, "签名验证失败", raw_payload)
        return PlainTextResponse(content="failure", status_code=400)

    if trade_status != "TRADE_SUCCESS":
        await _record_callback_event(db, "ikunpay", order_no, trade_no, amount, verified, f"trade_status={trade_status}", raw_payload)
        return PlainTextResponse(content="success")

    try:
        order = await payment_service.mark_order_paid(db, order_no=order_no, payment_method="ikunpay", trade_no=trade_no)
        await _record_callback_event(db, "ikunpay", order_no, trade_no, amount, verified, None, raw_payload)
    except ValueError as e:
        await _record_callback_event(db, "ikunpay", order_no, trade_no, amount, verified, str(e), raw_payload)

    return PlainTextResponse(content="success")


@router.post("/callback/wechat/notify")
async def wechat_notify(request: Request, db: AsyncSession = Depends(get_db)):
    import json

    body = await request.body()
    raw_payload = body.decode("utf-8", errors="replace")

    try:
        data = json.loads(raw_payload)
    except json.JSONDecodeError:
        return PlainTextResponse(content="failure", status_code=400)

    order_no = data.get("out_trade_no", "")
    trade_no = data.get("transaction_id", "")
    result_code = data.get("result_code", "")

    try:
        amount = float(data.get("total", 0)) / 100
    except (ValueError, TypeError):
        amount = 0.0

    if result_code != "SUCCESS":
        await _record_callback_event(db, "wechat", order_no, trade_no, amount, True, f"result_code={result_code}", raw_payload)
        return PlainTextResponse(content="success")

    try:
        order = await payment_service.mark_order_paid(db, order_no=order_no, payment_method="wechat", trade_no=trade_no)
        await _record_callback_event(db, "wechat", order_no, trade_no, amount, True, None, raw_payload)
    except ValueError as e:
        await _record_callback_event(db, "wechat", order_no, trade_no, amount, True, str(e), raw_payload)

    return PlainTextResponse(content="success")
