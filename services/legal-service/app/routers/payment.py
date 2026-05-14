import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import AsyncSessionLocal
from ..models import ConsultationPayment, LawyerWallet, WalletTransaction, Consultation
from ..middleware.auth import get_current_user, AuthUser
from ..schemas.response import ApiResponse

router = APIRouter()


class CreatePaymentRequest(BaseModel):
    consultation_id: int
    amount: float
    pay_method: str = "wechat"


class PaymentCallbackRequest(BaseModel):
    order_no: str
    transaction_id: str
    pay_method: str = "wechat"


class PaymentResponse(BaseModel):
    id: int
    consultation_id: int
    order_no: str
    amount: float
    platform_fee: float
    lawyer_income: float
    pay_method: str
    status: str
    paid_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def _generate_order_no() -> str:
    return f"CONSULT{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_payment(
    body: CreatePaymentRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    consultation_result = await db.execute(
        select(Consultation).where(Consultation.id == body.consultation_id)
    )
    consultation = consultation_result.scalar_one_or_none()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    existing = await db.execute(
        select(ConsultationPayment).where(
            ConsultationPayment.consultation_id == body.consultation_id,
            ConsultationPayment.status != "refunded"
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="该咨询已有进行中的支付订单")

    platform_fee = round(body.amount * 0.15, 2)
    lawyer_income = round(body.amount - platform_fee, 2)

    payment = ConsultationPayment(
        consultation_id=body.consultation_id,
        order_no=_generate_order_no(),
        amount=body.amount,
        platform_fee=platform_fee,
        lawyer_income=lawyer_income,
        pay_method=body.pay_method,
        status="pending",
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return ApiResponse.success(PaymentResponse.model_validate(payment))


@router.post("/callback")
async def payment_callback(
    body: PaymentCallbackRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    result = await db.execute(
        select(ConsultationPayment).where(ConsultationPayment.order_no == body.order_no)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status != "pending":
        raise HTTPException(status_code=409, detail=f"订单状态不可支付: {payment.status}")

    payment.status = "paid"
    payment.paid_at = datetime.now(timezone.utc)

    consultation_result = await db.execute(
        select(Consultation).where(Consultation.id == payment.consultation_id)
    )
    consultation = consultation_result.scalar_one_or_none()

    if consultation and consultation.lawyer_id:
        wallet_result = await db.execute(
            select(LawyerWallet).where(LawyerWallet.lawyer_id == consultation.lawyer_id)
        )
        wallet = wallet_result.scalar_one_or_none()
        if wallet:
            wallet.frozen_balance += payment.lawyer_income
            txn = WalletTransaction(
                wallet_id=wallet.id,
                type="freeze",
                amount=payment.lawyer_income,
                balance_after=wallet.balance,
                order_no=payment.order_no,
                payment_id=payment.id,
                description=f"咨询#{payment.consultation_id} 支付冻结",
            )
            db.add(txn)

    await db.commit()
    await db.refresh(payment)
    return ApiResponse.success(PaymentResponse.model_validate(payment))


@router.post("/{payment_id}/refund")
async def refund_payment(
    payment_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    result = await db.execute(
        select(ConsultationPayment).where(ConsultationPayment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status != "paid":
        raise HTTPException(status_code=409, detail=f"订单状态不可退款: {payment.status}")

    consultation_result = await db.execute(
        select(Consultation).where(Consultation.id == payment.consultation_id)
    )
    consultation = consultation_result.scalar_one_or_none()
    if not consultation or consultation.user_id != current_user.id:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="无权操作此退款")

    payment.status = "refunding"

    if consultation and consultation.lawyer_id:
        wallet_result = await db.execute(
            select(LawyerWallet).where(LawyerWallet.lawyer_id == consultation.lawyer_id)
        )
        wallet = wallet_result.scalar_one_or_none()
        if wallet and wallet.frozen_balance >= payment.lawyer_income:
            wallet.frozen_balance -= payment.lawyer_income
            txn = WalletTransaction(
                wallet_id=wallet.id,
                type="refund",
                amount=-payment.lawyer_income,
                balance_after=wallet.balance,
                order_no=payment.order_no,
                payment_id=payment.id,
                description=f"咨询#{payment.consultation_id} 退款解冻",
            )
            db.add(txn)

    payment.status = "refunded"
    payment.refunded_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(payment)
    return ApiResponse.success(PaymentResponse.model_validate(payment))


@router.get("/order/{order_no}")
async def get_order(
    order_no: str,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    result = await db.execute(
        select(ConsultationPayment).where(ConsultationPayment.order_no == order_no)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return ApiResponse.success(PaymentResponse.model_validate(payment))


@router.post("/{payment_id}/settle")
async def settle_payment(
    payment_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    result = await db.execute(
        select(ConsultationPayment).where(ConsultationPayment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status != "paid":
        raise HTTPException(status_code=409, detail=f"订单状态不可结算: {payment.status}")

    if current_user.role not in ("admin", "lawyer"):
        raise HTTPException(status_code=403, detail="无权操作结算")

    consultation_result = await db.execute(
        select(Consultation).where(Consultation.id == payment.consultation_id)
    )
    consultation = consultation_result.scalar_one_or_none()

    if consultation and consultation.lawyer_id:
        wallet_result = await db.execute(
            select(LawyerWallet).where(LawyerWallet.lawyer_id == consultation.lawyer_id)
        )
        wallet = wallet_result.scalar_one_or_none()
        if wallet and wallet.frozen_balance >= payment.lawyer_income:
            wallet.frozen_balance -= payment.lawyer_income
            wallet.balance += payment.lawyer_income
            wallet.total_income += payment.lawyer_income
            txn = WalletTransaction(
                wallet_id=wallet.id,
                type="income",
                amount=payment.lawyer_income,
                balance_after=wallet.balance,
                order_no=payment.order_no,
                payment_id=payment.id,
                description=f"咨询#{payment.consultation_id} 结算收入",
            )
            db.add(txn)

    payment.status = "settled"
    payment.settled_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(payment)
    return ApiResponse.success(PaymentResponse.model_validate(payment))