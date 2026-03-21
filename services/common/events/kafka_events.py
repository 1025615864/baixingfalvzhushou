"""Kafka 事件定义

定义服务间通信的事件结构。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import json


class EventType(str, Enum):
    # 用户事件
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_PROFILE_UPDATED = "user.profile_updated"

    # 支付事件
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_REFUNDED = "payment.refunded"
    PAYMENT_FAILED = "payment.failed"
    SETTLEMENT_COMPLETED = "settlement.completed"

    # 咨询事件
    CONSULTATION_CREATED = "legal.consultation.created"
    CONSULTATION_COMPLETED = "legal.consultation.completed"
    LAWYER_VERIFIED = "legal.lawyer.verified"

    # 积分事件
    POINTS_CHANGED = "points.changed"
    POINTS_EXPIRED = "points.expired"

    # 通知事件
    NOTIFICATION_PUSH = "notification.push"
    NOTIFICATION_EMAIL = "notification.email"


@dataclass
class DomainEvent:
    """领域事件基类"""

    event_id: str = field(default="")
    event_type: str = ""
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainEvent":
        return cls(
            event_id=data.get("event_id", ""),
            event_type=data.get("event_type", ""),
            occurred_at=datetime.fromisoformat(data["occurred_at"])
                if "occurred_at" in data else datetime.utcnow(),
            version=data.get("version", "1.0"),
            metadata=data.get("metadata", {}),
        )


# ==================== 用户事件 ====================

@dataclass
class UserRegisteredEvent(DomainEvent):
    """用户注册事件"""

    event_type: str = EventType.USER_REGISTERED.value
    user_id: int = 0
    phone: str = ""
    email: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update({
            "user_id": self.user_id,
            "phone": self.phone,
            "email": self.email,
        })
        return data


# ==================== 支付事件 ====================

@dataclass
class PaymentCompletedEvent(DomainEvent):
    """支付完成事件"""

    event_type: str = EventType.PAYMENT_COMPLETED.value
    order_id: str = ""
    user_id: int = 0
    amount: float = 0.0
    payment_method: str = ""
    trade_no: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update({
            "order_id": self.order_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "payment_method": self.payment_method,
            "trade_no": self.trade_no,
        })
        return data


@dataclass
class PaymentRefundedEvent(DomainEvent):
    """退款完成事件"""

    event_type: str = EventType.PAYMENT_REFUNDED.value
    order_id: str = ""
    user_id: int = 0
    refund_amount: float = 0.0
    refund_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update({
            "order_id": self.order_id,
            "user_id": self.user_id,
            "refund_amount": self.refund_amount,
            "refund_reason": self.refund_reason,
        })
        return data


# ==================== 咨询事件 ====================

@dataclass
class ConsultationCompletedEvent(DomainEvent):
    """咨询完成事件"""

    event_type: str = EventType.CONSULTATION_COMPLETED.value
    consultation_id: int = 0
    user_id: int = 0
    lawyer_id: int = 0
    duration_minutes: int = 0

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update({
            "consultation_id": self.consultation_id,
            "user_id": self.user_id,
            "lawyer_id": self.lawyer_id,
            "duration_minutes": self.duration_minutes,
        })
        return data


@dataclass
class LawyerVerifiedEvent(DomainEvent):
    """律师认证通过事件"""

    event_type: str = EventType.LAWYER_VERIFIED.value
    lawyer_id: int = 0
    lawyer_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update({
            "lawyer_id": self.lawyer_id,
            "lawyer_name": self.lawyer_name,
        })
        return data


# ==================== 积分事件 ====================

@dataclass
class PointsChangedEvent(DomainEvent):
    """积分变动事件"""

    event_type: str = EventType.POINTS_CHANGED.value
    user_id: int = 0
    change: int = 0
    balance: int = 0
    source: str = ""
    reference_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update({
            "user_id": self.user_id,
            "change": self.change,
            "balance": self.balance,
            "source": self.source,
            "reference_id": self.reference_id,
        })
        return data


# ==================== Topic 定义 ====================

class Topic:
    """Kafka Topic 定义"""

    USER = "domain.user"
    PAYMENT = "domain.payment"
    LEGAL = "domain.legal"
    POINTS = "domain.points"
    NOTIFICATION = "domain.notification"

    @classmethod
    def for_event(cls, event_type: str) -> str:
        """根据事件类型获取Topic"""
        prefix = event_type.split(".")[0]
        topic_map = {
            "user": cls.USER,
            "payment": cls.PAYMENT,
            "legal": cls.LEGAL,
            "points": cls.POINTS,
            "notification": cls.NOTIFICATION,
        }
        return topic_map.get(prefix, cls.USER)
