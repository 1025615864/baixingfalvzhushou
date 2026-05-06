"""Payment Channel Service Kafka 事件定义"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Any, Dict
import json
import uuid


@dataclass
class PaymentEvent:
    event_id: str
    event_type: str
    timestamp: str
    version: str
    source: str
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    user_id: Optional[str] = None
    amount: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "PaymentEvent":
        return cls(**json.loads(data))


class PaymentEventTypes:
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    PAYMENT_CANCELLED = "payment.cancelled"


class PaymentEventBus:
    def __init__(self, producer_client):
        self._producer = producer_client

    async def publish_payment_event(self, event: PaymentEvent, key: Optional[str] = None):
        await self._producer.send(
            topic="baixing.payment.events",
            value=event.to_json(),
            key=key,
        )

    async def publish_order_event(self, event: PaymentEvent, order_id: str):
        await self.publish_payment_event(event, key=order_id)


def create_payment_event(
    event_type: str,
    order_id: Optional[str] = None,
    payment_id: Optional[str] = None,
    user_id: Optional[str] = None,
    amount: Optional[int] = None,
    payload: Optional[Dict[str, Any]] = None,
    source: str = "payment-channel-service",
) -> PaymentEvent:
    return PaymentEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.utcnow().isoformat(),
        version="1.0",
        source=source,
        order_id=order_id,
        payment_id=payment_id,
        user_id=user_id,
        amount=amount,
        payload=payload or {},
    )
