"""Order Payment Saga - 带持久化的订单支付流程"""

import httpx
import logging
import os
import uuid
from typing import Dict, Any, Optional

from services.common.saga import (
    SagaStep,
    SagaState,
    SagaStatus,
)
from .persistent_saga import (
    PersistentSagaOrchestrator,
    get_persistence,
    init_saga_persistence,
    close_saga_persistence,
)

logger = logging.getLogger(__name__)

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8004")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8002")
POINTS_SERVICE_URL = os.getenv("POINTS_SERVICE_URL", "http://localhost:8012")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")


class PaymentResult:
    def __init__(
        self,
        payment_id: str,
        success: bool,
        transaction_id: Optional[str] = None,
    ):
        self.payment_id = payment_id
        self.success = success
        self.transaction_id = transaction_id


class OrderPaymentSaga:
    """订单支付 SAGA - 带持久化"""

    def __init__(
        self,
        order_id: str,
        user_id: str,
        amount: int,
        items: list,
    ):
        self.order_id = order_id
        self.user_id = user_id
        self.amount = amount
        self.items = items
        self.payment_result: Optional[PaymentResult] = None

    def _create_steps(self):
        return [
            SagaStep(
                name="create_order",
                forward=self._create_order,
                compensate=self._compensate_order,
                retry_count=3,
                timeout=10.0,
            ),
            SagaStep(
                name="process_payment",
                forward=self._process_payment,
                compensate=self._compensate_payment,
                retry_count=3,
                timeout=30.0,
            ),
            SagaStep(
                name="award_points",
                forward=self._award_points,
                compensate=self._compensate_points,
                retry_count=2,
                timeout=10.0,
            ),
        ]

    async def execute(self) -> SagaState:
        """执行带持久化的 SAGA"""
        saga = PersistentSagaOrchestrator(
            saga_id=f"order_saga_{self.order_id}",
            steps=self._create_steps(),
            description=f"Order payment for order {self.order_id}",
            persistence=await get_persistence(),
        )

        result = await saga.execute()
        return result

    async def _create_order(self) -> Dict[str, Any]:
        logger.info(f"[SAGA] Creating order: {self.order_id}")
        order_data = {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "items": self.items,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ORDER_SERVICE_URL}/api/v1/orders",
                json=order_data,
            )
            if response.status_code not in (200, 201):
                raise Exception(f"Create order failed: {response.text}")
            result = response.json()
            return {"order_id": result.get("id"), "order_no": result.get("order_no")}

    async def _compensate_order(self, result: Dict[str, Any]):
        order_no = result.get("order_no") if result else None
        if not order_no:
            return
        logger.info(f"[SAGA] Compensating order: {order_no}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                await client.delete(
                    f"{ORDER_SERVICE_URL}/api/v1/orders/{order_no}/cancel",
                )
            except Exception as e:
                logger.error(f"Compensate order failed: {e}")

    async def _process_payment(self) -> Dict[str, Any]:
        logger.info(f"[SAGA] Processing payment for order: {self.order_id}")
        payment_method = "alipay"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{PAYMENT_SERVICE_URL}/api/v1/payment/create",
                json={
                    "order_no": self.order_id,
                    "amount": self.amount,
                    "payment_method": payment_method,
                    "subject": f"订单 {self.order_id}",
                },
            )
            if response.status_code not in (200, 201):
                raise Exception(f"Process payment failed: {response.text}")
            result = response.json()
            payment_id = result.get("payment_id")
            self.payment_result = PaymentResult(
                payment_id=payment_id,
                success=True,
                transaction_id=result.get("transaction_id"),
            )
            return {"payment_id": payment_id, "payment_url": result.get("payment_url")}

    async def _compensate_payment(self, result: Dict[str, Any]):
        payment_id = result.get("payment_id") if result else None
        if not payment_id:
            return
        logger.info(f"[SAGA] Compensating payment: {payment_id}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                await client.post(
                    f"{PAYMENT_SERVICE_URL}/api/v1/payment/{payment_id}/refund",
                    json={"reason": "Saga compensation"},
                )
            except Exception as e:
                logger.error(f"Compensate payment failed: {e}")

    async def _award_points(self) -> Dict[str, Any]:
        logger.info(f"[SAGA] Awarding points for order: {self.order_id}")
        points = int(self.amount * 10)
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                await client.post(
                    f"{POINTS_SERVICE_URL}/api/v1/points/earn",
                    json={"user_id": self.user_id, "points": points, "source": "order_complete"},
                )
            except Exception as e:
                logger.warning(f"Award points failed (non-critical): {e}")
        return {"points_awarded": points}

    async def _compensate_points(self, result: Dict[str, Any]):
        points = result.get("points_awarded") if result else 0
        if not points:
            return
        logger.info(f"[SAGA] Compensating {points} points for user {self.user_id}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                await client.post(
                    f"{POINTS_SERVICE_URL}/api/v1/points/deduct",
                    json={"user_id": self.user_id, "points": points, "source": "saga_compensation"},
                )
            except Exception as e:
                logger.error(f"Compensate points failed: {e}")


__all__ = [
    "OrderPaymentSaga",
    "init_saga_persistence",
    "close_saga_persistence",
    "get_persistence",
    "PersistentSagaOrchestrator",
]
