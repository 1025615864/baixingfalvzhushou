from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Any, Dict
import json
import uuid


@dataclass
class BaseEvent:
    event_id: str
    event_type: str
    timestamp: str
    version: str
    source: str

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "BaseEvent":
        return cls(**json.loads(data))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UserEvent(BaseEvent):
    user_id: str
    payload: Dict[str, Any]

    def __init__(
        self,
        event_type: str,
        user_id: str,
        payload: Dict[str, Any],
        source: str,
    ):
        super().__init__(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0",
            source=source,
        )
        self.user_id = user_id
        self.payload = payload


@dataclass
class PaymentEvent(BaseEvent):
    payment_id: str
    user_id: str
    amount: int
    status: str
    payload: Dict[str, Any]

    def __init__(
        self,
        event_type: str,
        payment_id: str,
        user_id: str,
        amount: int,
        status: str,
        payload: Dict[str, Any],
        source: str,
    ):
        super().__init__(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0",
            source=source,
        )
        self.payment_id = payment_id
        self.user_id = user_id
        self.amount = amount
        self.status = status
        self.payload = payload


@dataclass
class OrderEvent(BaseEvent):
    order_id: str
    user_id: str
    amount: int
    status: str
    items: list

    def __init__(
        self,
        event_type: str,
        order_id: str,
        user_id: str,
        amount: int,
        status: str,
        items: list,
        source: str,
    ):
        super().__init__(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0",
            source=source,
        )
        self.order_id = order_id
        self.user_id = user_id
        self.amount = amount
        self.status = status
        self.items = items


class UserEventTypes:
    USER_REGISTERED = "user.registered"
    USER_UPDATED = "user.updated"
    USER_STATUS_CHANGED = "user.status_changed"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    MEMBERSHIP_ACTIVATED = "user.membership_activated"
    QUOTA_CHANGED = "user.quota_changed"


class PaymentEventTypes:
    PAYMENT_CREATED = "payment.created"
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    PAYMENT_PENDING = "payment.pending"


class OrderEventTypes:
    ORDER_CREATED = "order.created"
    ORDER_PAID = "order.paid"
    ORDER_COMPLETED = "order.completed"
    ORDER_CANCELLED = "order.cancelled"
