from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, cast
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

from ...database import get_db
from ...models.payment import PaymentOrder, PaymentStatus
from ...models.user import User
from ...utils.deps import get_current_user
from ...core.money import quantize_amount, amount_to_cents, Money
from . import helpers as payment_helpers

router = APIRouter()


class CreateOrderRequest(BaseModel):
    order_type: str
    amount: Decimal
    title: str
    description: str | None = None
    related_id: int | None = None
    related_type: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "order_type": "consultation",
                    "amount": 99.00,
                    "title": "法律咨询",
                    "description": "一次法律咨询服务",
                }
            ]
        }
    }


@router.post("/orders", summary="创建订单")
async def create_order(
    data: CreateOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """创建支付订单"""
    if data.order_type not in {
        "consultation",
        "service",
        "vip",
        "recharge",
        "ai_pack",
            "light_consult_review"}:
        raise HTTPException(status_code=400, detail="无效的订单类型")

    related_id = data.related_id
    related_type = data.related_type

    if data.order_type == "vip":
        vip_days, vip_price = await payment_helpers._get_vip_plan(db)
        amount = payment_helpers._quantize_amount(vip_price)
        title = f"VIP会员（{int(vip_days)}天）"
        description = data.description
    elif data.order_type == "ai_pack":
        related_type = str(getattr(data, "related_type", "")
                           or "").strip().lower() or "ai_chat"
        if related_type not in payment_helpers.AI_PACK_RELATED_TYPES:
            raise HTTPException(status_code=400, detail="无效的次数包类型")

        related_id_raw: object | None = cast(
            object | None, getattr(
                data, "related_id", None))
        pack_count: int | None = None
        if isinstance(related_id_raw, bool) or related_id_raw is None:
            pack_count = None
        elif isinstance(related_id_raw, int):
            pack_count = related_id_raw
        elif isinstance(related_id_raw, float):
            pack_count = int(related_id_raw)
        elif isinstance(related_id_raw, str) and related_id_raw.strip():
            try:
                pack_count = int(related_id_raw.strip())
            except Exception:
                logger.exception("Failed to parse pack_count")
                pack_count = None

        options = await payment_helpers._get_pack_options(db, related_type)
        if pack_count is None or pack_count not in options:
            raise HTTPException(status_code=400, detail="无效的次数包")

        related_id = int(pack_count)

        amount = payment_helpers._quantize_amount(options[int(pack_count)])
        title = (
            f"文书生成次数包（{int(pack_count)}次）"
            if related_type == "document_generate"
            else f"AI咨询次数包（{int(pack_count)}次）"
        )
        description = data.description
    elif data.order_type == "light_consult_review":
        related_type = str(getattr(data, "related_type", "")
                           or "").strip().lower() or "ai_consultation"
        if related_type != "ai_consultation":
            raise HTTPException(status_code=400, detail="无效的关联类型")

        consultation_id_raw: object | None = cast(
            object | None, getattr(data, "related_id", None))
        consultation_id: int | None = None
        if isinstance(consultation_id_raw,
                      bool) or consultation_id_raw is None:
            consultation_id = None
        elif isinstance(consultation_id_raw, int):
            consultation_id = consultation_id_raw
        elif isinstance(consultation_id_raw, float):
            consultation_id = int(consultation_id_raw)
        elif isinstance(consultation_id_raw, str) and consultation_id_raw.strip():
            try:
                consultation_id = int(consultation_id_raw.strip())
            except Exception:
                logger.exception("Failed to parse consultation_id")
                consultation_id = None

        if consultation_id is None or consultation_id <= 0:
            raise HTTPException(status_code=400, detail="缺少咨询ID")

        from ...models.consultation import Consultation

        c_res = await db.execute(select(Consultation).where(Consultation.id == int(consultation_id)))
        c = c_res.scalar_one_or_none()
        if c is None:
            raise HTTPException(status_code=404, detail="咨询记录不存在")
        if int(getattr(c, "user_id", 0) or 0) != int(current_user.id):
            raise HTTPException(status_code=403, detail="无权限购买该咨询的复核")

        related_id = int(consultation_id)
        related_type = "ai_consultation"

        amount = payment_helpers._quantize_amount(await payment_helpers._get_review_price(db))
        title = "AI咨询律师复核"
        description = data.description
    else:
        amount = payment_helpers._quantize_amount(data.amount)
        title = data.title
        description = data.description

    amount_cents = amount_to_cents(amount)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="金额必须大于0")

    money_amount = Money(amount)

    order = PaymentOrder(
        order_no=payment_helpers.generate_order_no(),
        user_id=current_user.id,
        order_type=data.order_type,
        amount=money_amount.to_float(),
        actual_amount=money_amount.to_float(),
        amount_cents=amount_cents,
        actual_amount_cents=amount_cents,
        status=PaymentStatus.PENDING,
        title=title,
        description=description,
        related_id=related_id,
        related_type=related_type,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    return {
        "order_id": order.id,
        "order_no": order.order_no,
        "amount": order.actual_amount,
        "expires_at": order.expires_at,
    }


@router.get("/pricing", summary="获取商业化价格表")
async def get_pricing(db: Annotated[AsyncSession, Depends(get_db)]):
    vip_days, vip_price = await payment_helpers._get_vip_plan(db)
    ai_options = await payment_helpers._get_pack_options(db, "ai_chat")
    doc_options = await payment_helpers._get_pack_options(db, "document_generate")
    review_price = await payment_helpers._get_review_price(db)

    def _to_list(options: dict[int, float]):
        return [
            {"count": int(k), "price": float(v)}
            for k, v in sorted(options.items(), key=lambda kv: int(kv[0]))
        ]

    return {
        "vip": {"days": int(vip_days), "price": float(vip_price)},
        "services": {
            "light_consult_review": {"price": float(review_price)},
        },
        "packs": {
            "ai_chat": _to_list(ai_options),
            "document_generate": _to_list(doc_options),
        },
    }
