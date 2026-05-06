"""Points Service - Kafka 消费者

消费事件，处理积分变动
"""

import asyncio
import logging
from typing import Dict, Any

from services.common.events.consumer import BaseConsumer, Message
from services.common.events import PaymentEventTypes

logger = logging.getLogger(__name__)


class PointsConsumer(BaseConsumer):
    """积分服务 Kafka 消费者"""

    def __init__(self, bootstrap_servers: str):
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            group_id="points-service",
            topics=[
                "baixing.payment.events",
                "baixing.user.events",
            ],
            dead_letter_topic="baixing.points.dlq",
        )

        self._points_balances: Dict[str, int] = {}

    async def start(self):
        """启动消费者并注册处理器"""
        await super().start()

        self.register_handler(PaymentEventTypes.PAYMENT_SUCCESS, self._handle_payment_success)
        self.register_handler(PaymentEventTypes.PAYMENT_REFUNDED, self._handle_payment_refunded)

        logger.info("Points consumer handlers registered")

    async def _handle_payment_success(self, message: Message):
        """处理支付成功 - 发放积分"""
        user_id = message.value.get("user_id")
        amount = message.value.get("amount", 0)

        points_earned = amount // 100

        current_balance = self._points_balances.get(user_id, 0)
        new_balance = current_balance + points_earned

        self._points_balances[user_id] = new_balance

        logger.info(
            f"Points awarded: user={user_id}, amount={points_earned}, new_balance={new_balance}"
        )

        await self._save_points_record(user_id, points_earned, "earned", message.event_id)

    async def _handle_payment_refunded(self, message: Message):
        """处理退款 - 扣除积分"""
        user_id = message.value.get("user_id")
        amount = message.value.get("amount", 0)

        points_deducted = amount // 100

        current_balance = self._points_balances.get(user_id, 0)
        new_balance = max(0, current_balance - points_deducted)

        self._points_balances[user_id] = new_balance

        logger.info(
            f"Points deducted: user={user_id}, amount={points_deducted}, new_balance={new_balance}"
        )

        await self._save_points_record(user_id, points_deducted, "deducted", message.event_id)

    async def _save_points_record(
        self,
        user_id: str,
        points: int,
        action: str,
        event_id: str,
    ):
        """保存积分变动记录"""
        logger.debug(f"Points record saved: user={user_id}, points={points}, action={action}")

    def get_balance(self, user_id: str) -> int:
        """获取用户积分余额"""
        return self._points_balances.get(user_id, 0)


async def run_points_consumer(bootstrap_servers: str = "localhost:9092"):
    """运行积分消费者"""
    logging.basicConfig(level=logging.INFO)

    consumer = PointsConsumer(bootstrap_servers)

    try:
        await consumer.start()
        await consumer.run()
    except KeyboardInterrupt:
        logger.info("Shutting down points consumer...")
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(run_points_consumer())
