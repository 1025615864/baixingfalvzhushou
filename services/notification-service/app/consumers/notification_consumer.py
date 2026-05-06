"""Notification Service - Kafka 消费者

消费用户事件，发送通知
"""

import asyncio
import logging
from typing import Dict, Any

from services.common.events.consumer import BaseConsumer, Message
from services.common.events import (
    UserEventTypes,
    PaymentEventTypes,
)

logger = logging.getLogger(__name__)


class NotificationConsumer(BaseConsumer):
    """通知服务 Kafka 消费者"""

    def __init__(self, bootstrap_servers: str):
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            group_id="notification-service",
            topics=[
                "baixing.user.events",
                "baixing.payment.events",
            ],
            dead_letter_topic="baixing.notification.dlq",
        )

        self._notification_queue: list = []

    async def start(self):
        """启动消费者并注册处理器"""
        await super().start()

        self.register_handler(UserEventTypes.USER_REGISTERED, self._handle_user_registered)
        self.register_handler(UserEventTypes.USER_LOGIN, self._handle_user_login)
        self.register_handler(UserEventTypes.MEMBERSHIP_ACTIVATED, self._handle_membership_activated)
        self.register_handler(PaymentEventTypes.PAYMENT_SUCCESS, self._handle_payment_success)
        self.register_handler(PaymentEventTypes.PAYMENT_FAILED, self._handle_payment_failed)

        logger.info("Notification consumer handlers registered")

    async def _handle_user_registered(self, message: Message):
        """处理用户注册事件"""
        user_id = message.value.get("user_id")
        payload = message.value.get("payload", {})

        notification = {
            "type": "welcome",
            "user_id": user_id,
            "title": "欢迎注册百姓法律助手",
            "content": f"亲爱的{payload.get('username', '用户')}，感谢您注册！",
            "channel": "email",
        }

        await self._send_notification(notification)
        logger.info(f"Welcome notification sent to user {user_id}")

    async def _handle_user_login(self, message: Message):
        """处理用户登录事件"""
        user_id = message.value.get("user_id")
        payload = message.value.get("payload", {})

        notification = {
            "type": "login_alert",
            "user_id": user_id,
            "title": "登录提醒",
            "content": f"您的账号于{payload.get('login_time', '刚刚')}在新设备登录",
            "channel": "push",
        }

        await self._send_notification(notification)
        logger.info(f"Login alert notification sent to user {user_id}")

    async def _handle_membership_activated(self, message: Message):
        """处理会员激活事件"""
        user_id = message.value.get("user_id")
        payload = message.value.get("payload", {})

        notification = {
            "type": "membership_activated",
            "user_id": user_id,
            "title": "会员开通成功",
            "content": f"您的{payload.get('membership_type', '会员')}已开通，有效期至{payload.get('expire_at', '未知')}",
            "channel": "sms",
        }

        await self._send_notification(notification)
        logger.info(f"Membership notification sent to user {user_id}")

    async def _handle_payment_success(self, message: Message):
        """处理支付成功事件"""
        user_id = message.value.get("user_id")
        amount = message.value.get("amount", 0)

        notification = {
            "type": "payment_success",
            "user_id": user_id,
            "title": "支付成功",
            "content": f"您已成功支付{amount / 100:.2f}元",
            "channel": "push",
        }

        await self._send_notification(notification)
        logger.info(f"Payment success notification sent to user {user_id}")

    async def _handle_payment_failed(self, message: Message):
        """处理支付失败事件"""
        user_id = message.value.get("user_id")
        reason = message.value.get("payload", {}).get("reason", "未知原因")

        notification = {
            "type": "payment_failed",
            "user_id": user_id,
            "title": "支付失败",
            "content": f"您的支付失败，原因：{reason}。请重试或联系客服。",
            "channel": "push",
        }

        await self._send_notification(notification)
        logger.info(f"Payment failed notification sent to user {user_id}")

    async def _send_notification(self, notification: Dict[str, Any]):
        """发送通知"""
        self._notification_queue.append(notification)
        logger.debug(f"Notification queued: {notification['type']} to {notification['user_id']}")


async def run_notification_consumer(bootstrap_servers: str = "localhost:9092"):
    """运行通知消费者"""
    logging.basicConfig(level=logging.INFO)

    consumer = NotificationConsumer(bootstrap_servers)

    try:
        await consumer.start()
        await consumer.run()
    except KeyboardInterrupt:
        logger.info("Shutting down notification consumer...")
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(run_notification_consumer())
