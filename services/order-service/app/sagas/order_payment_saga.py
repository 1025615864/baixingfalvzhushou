"""Order Payment Saga - 带持久化的订单支付流程"""

import asyncio
import logging
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
        self.inventory_result: Optional[Dict] = None

    def _create_steps(self):
        return [
            SagaStep(
                name="create_order",
                forward=self._create_order,
                compensate=self._cancel_order,
                retry_count=3,
                timeout=10.0,
            ),
            SagaStep(
                name="reserve_inventory",
                forward=self._reserve_inventory,
                compensate=self._release_inventory,
                retry_count=2,
                timeout=15.0,
            ),
            SagaStep(
                name="process_payment",
                forward=self._process_payment,
                compensate=self._refund_payment,
                retry_count=3,
                timeout=30.0,
            ),
            SagaStep(
                name="award_points",
                forward=self._award_points,
                compensate=self._deduct_points,
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
        await asyncio.sleep(0.1)

        order = {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "items": self.items,
            "status": "pending",
        }

        logger.info(f"[SAGA] Order created: {self.order_id}")
        return order

    async def _cancel_order(self, result: Dict[str, Any]):
        logger.info(f"[SAGA] Cancelling order: {result.get('order_id')}")
        await asyncio.sleep(0.1)
        logger.info(f"[SAGA] Order cancelled")

    async def _reserve_inventory(self) -> Dict[str, Any]:
        logger.info(f"[SAGA] Reserving inventory for order: {self.order_id}")
        await asyncio.sleep(0.1)

        inventory_id = str(uuid.uuid4())
        self.inventory_result = {
            "inventory_id": inventory_id,
            "order_id": self.order_id,
            "items_reserved": len(self.items),
        }

        logger.info(f"[SAGA] Inventory reserved: {inventory_id}")
        return self.inventory_result

    async def _release_inventory(self, result: Dict[str, Any]):
        inventory_id = result.get("inventory_id") if result else self.inventory_result.get("inventory_id")
        logger.info(f"[SAGA] Releasing inventory: {inventory_id}")
        await asyncio.sleep(0.1)
        logger.info(f"[SAGA] Inventory released")

    async def _process_payment(self) -> Dict[str, Any]:
        logger.info(f"[SAGA] Processing payment for order: {self.order_id}")
        await asyncio.sleep(0.1)

        payment_id = f"pay_{self.order_id}"
        self.payment_result = PaymentResult(
            payment_id=payment_id,
            success=True,
            transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
        )

        result = {
            "payment_id": payment_id,
            "success": True,
            "transaction_id": self.payment_result.transaction_id,
        }

        logger.info(f"[SAGA] Payment processed: {payment_id}")
        return result

    async def _refund_payment(self, result: Dict[str, Any]):
        payment_id = result.get("payment_id") if result else self.payment_result.payment_id
        logger.info(f"[SAGA] Refunding payment: {payment_id}")
        await asyncio.sleep(0.1)
        logger.info(f"[SAGA] Payment refunded")

    async def _award_points(self) -> Dict[str, Any]:
        logger.info(f"[SAGA] Awarding points for order: {self.order_id}")
        await asyncio.sleep(0.1)

        points = self.amount // 100

        result = {
            "user_id": self.user_id,
            "points_awarded": points,
            "order_id": self.order_id,
        }

        logger.info(f"[SAGA] Points awarded: {points} to user {self.user_id}")
        return result

    async def _deduct_points(self, result: Dict[str, Any]):
        points = result.get("points_awarded") if result else 0
        logger.info(f"[SAGA] Deducting {points} points from user {self.user_id}")
        await asyncio.sleep(0.1)
        logger.info(f"[SAGA] Points deducted")


__all__ = [
    "OrderPaymentSaga",
    "init_saga_persistence",
    "close_saga_persistence",
    "get_persistence",
    "PersistentSagaOrchestrator",
]
