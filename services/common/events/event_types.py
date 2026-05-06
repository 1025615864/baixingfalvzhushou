"""Kafka事件类型定义"""
from enum import Enum


class UserEventType(str, Enum):
    """用户相关事件类型"""
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_PROFILE_UPDATED = "user.profile.updated"
    USER_PASSWORD_CHANGED = "user.password.changed"
    USER_EMAIL_VERIFIED = "user.email.verified"
    USER_PHONE_VERIFIED = "user.phone.verified"
    USER_2FA_ENABLED = "user.2fa.enabled"
    USER_2FA_DISABLED = "user.2fa.disabled"
    USER_DEACTIVATED = "user.deactivated"
    USER_REACTIVATED = "user.reactivated"


class LawfirmEventType(str, Enum):
    """律所相关事件类型"""
    LAWFIRM_CREATED = "lawfirm.created"
    LAWFIRM_UPDATED = "lawfirm.updated"
    LAWYER_JOINED = "lawyer.joined"
    LAWYER_LEFT = "lawyer.left"


class PaymentEventType(str, Enum):
    """支付相关事件类型"""
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    REFUND_INITIATED = "refund.initiated"
    REFUND_COMPLETED = "refund.completed"
