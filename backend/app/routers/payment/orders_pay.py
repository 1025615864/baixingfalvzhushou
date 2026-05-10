from __future__ import annotations

import types
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Payment Orders Pay"])

from app.services.prometheus_metrics import prometheus_metrics


class _Legacy:
    PaymentStatus = type("PaymentStatus", (), {"PAID": "paid", "PENDING": "pending", "CANCELLED": "cancelled"})
    HTTPException = HTTPException
    select = lambda *_a, **_k: None
    update = lambda *_a, **_k: None
    PaymentOrder = None
    UserBalance = None
    func = None
    sa_cast = lambda expr, _typ: None
    Integer = None
    _quantize_amount = lambda v: float(v)
    _decimal_to_cents = lambda v: int(round(float(v) * 100))
    generate_order_no = lambda: "123"
    _maybe_apply_vip_membership_in_tx = None
    _maybe_apply_ai_pack_in_tx = None
    _maybe_confirm_lawyer_consultation_in_tx = None
    _maybe_create_consultation_review_task_in_tx = None
    BalanceTransaction = lambda **kwargs: kwargs
    _get_or_create_balance_in_tx = None
    settings = None
    _append_query_param = lambda url, k, v: f"{url}?{k}={v}"
    _ikunpay_build_submit_pay_url = lambda **_k: "PAYURL"
    _alipay_build_page_pay_url = lambda **_k: "ALIURL"


legacy = _Legacy()


async def pay_order(order_no: str, data, current_user=None, db=None):
    raise NotImplementedError


@router.post("/orders/{order_no}/pay")
async def pay_order_endpoint(order_no: str):
    raise NotImplementedError
