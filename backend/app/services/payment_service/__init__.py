"""Payment service."""
from __future__ import annotations
import enum
import time
from typing import Optional
from dataclasses import dataclass, field


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(enum.Enum):
    WECHAT = "wechat"
    ALIPAY = "alipay"
    BANK_CARD = "bank_card"


@dataclass
class Payment:
    id: str
    user_id: int
    amount: float
    status: PaymentStatus = PaymentStatus.PENDING
    method: Optional[PaymentMethod] = None
    description: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class PaymentService:
    def __init__(self):
        self._payments: dict[str, Payment] = {}
        self._next_id = 1

    async def create_payment(self, user_id: int, amount: float, method: Optional[PaymentMethod] = None, description: Optional[str] = None) -> Payment:
        payment_id = f"pay_{self._next_id}"
        self._next_id += 1
        payment = Payment(id=payment_id, user_id=user_id, amount=amount, method=method, description=description)
        self._payments[payment_id] = payment
        return payment

    async def get_payment(self, payment_id: str) -> Optional[Payment]:
        return self._payments.get(payment_id)

    async def process_payment(self, payment_id: str) -> dict:
        payment = self._payments.get(payment_id)
        if not payment:
            return {"success": False, "error": "支付不存在"}
        if payment.status != PaymentStatus.PENDING:
            return {"success": False, "error": "支付状态不正确"}
        payment.status = PaymentStatus.PROCESSING
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = time.time()
        return {"success": True, "payment_id": payment_id, "status": payment.status.value}

    async def refund_payment(self, payment_id: str) -> dict:
        payment = self._payments.get(payment_id)
        if not payment:
            return {"success": False, "error": "支付不存在"}
        if payment.status != PaymentStatus.COMPLETED:
            return {"success": False, "error": "支付状态不允许退款"}
        payment.status = PaymentStatus.REFUNDED
        return {"success": True, "payment_id": payment_id, "status": payment.status.value}

    async def get_user_payments(self, user_id: int) -> list[Payment]:
        return [p for p in self._payments.values() if p.user_id == user_id]


payment_service = PaymentService()
