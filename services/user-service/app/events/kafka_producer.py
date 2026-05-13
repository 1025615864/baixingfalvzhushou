"""Kafka 事件生产者 - 集成用户事件发布"""

import logging
from typing import Optional

try:
    from services.common.events import (
        EventBus,
        UserEvent,
        UserEventTypes,
        PaymentEvent,
        PaymentEventTypes,
        get_event_bus,
        init_event_bus,
        close_event_bus,
    )
except ImportError:
    EventBus = None
    UserEvent = None
    UserEventTypes = None
    PaymentEvent = None
    PaymentEventTypes = None
    get_event_bus = None
    init_event_bus = None
    close_event_bus = None

logger = logging.getLogger(__name__)

_event_bus: Optional[EventBus] = None


async def init_kafka_producer(bootstrap_servers: str = "kafka:9092"):
    global _event_bus
    if init_event_bus is None:
        logger.warning("services.common.events not available, Kafka producer disabled")
        return None
    _event_bus = await init_event_bus(bootstrap_servers)
    logger.info(f"Kafka producer initialized: {bootstrap_servers}")
    return _event_bus


async def close_kafka_producer():
    global _event_bus
    if _event_bus:
        if close_event_bus is not None:
            await close_event_bus()
        _event_bus = None
        logger.info("Kafka producer closed")


async def publish_user_registered(
    user_id: str,
    email: str,
    username: str,
) -> bool:
    """发布用户注册事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = UserEvent(
        event_type=UserEventTypes.USER_REGISTERED,
        user_id=user_id,
        payload={
            "email": email,
            "username": username,
        },
        source="user-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id=user_id)
        logger.info(f"Published user.registered event for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish user.registered event: {e}")
        return False


async def publish_user_login(
    user_id: str,
    ip_address: Optional[str] = None,
) -> bool:
    """发布用户登录事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = UserEvent(
        event_type=UserEventTypes.USER_LOGIN,
        user_id=user_id,
        payload={
            "ip_address": ip_address,
        },
        source="user-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id=user_id)
        logger.info(f"Published user.login event for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish user.login event: {e}")
        return False


async def publish_user_logout(
    user_id: str,
) -> bool:
    """发布用户登出事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = UserEvent(
        event_type=UserEventTypes.USER_LOGOUT,
        user_id=user_id,
        payload={},
        source="user-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id=user_id)
        logger.info(f"Published user.logout event for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish user.logout event: {e}")
        return False


async def publish_membership_activated(
    user_id: str,
    membership_type: str,
    expire_at: str,
) -> bool:
    """发布会员激活事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = UserEvent(
        event_type=UserEventTypes.MEMBERSHIP_ACTIVATED,
        user_id=user_id,
        payload={
            "membership_type": membership_type,
            "expire_at": expire_at,
        },
        source="user-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id=user_id)
        logger.info(f"Published user.membership_activated event for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish membership_activated event: {e}")
        return False


async def publish_quota_changed(
    user_id: str,
    quota_type: str,
    old_value: int,
    new_value: int,
    reason: Optional[str] = None,
) -> bool:
    """发布配额变更事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = PaymentEvent(
        event_type=PaymentEventTypes.QUOTA_CHANGED,
        user_id=user_id,
        payload={
            "quota_type": quota_type,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
        },
        source="user-service",
    )

    try:
        await _event_bus.publish_payment_event(event, user_id=user_id)
        logger.info(f"Published payment.quota_changed event for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish quota_changed event: {e}")
        return False


class UserEventTypesExt:
    PROFILE_UPDATED = "user.profile.updated"
    MEMBERSHIP_UPGRADED = "user.membership.upgraded"
    MEMBERSHIP_EXPIRED = "user.membership.expired"
    ACCOUNT_DELETED = "user.account.deleted"
    ACCOUNT_BANNED = "user.account.banned"
    ACCOUNT_UNBANNED = "user.account.unbanned"
    LAWYER_VERIFIED = "user.lawyer.verified"
    ROLE_CHANGED = "user.role.changed"


async def publish_profile_updated(
    user_id: str,
    nickname: Optional[str] = None,
    avatar: Optional[str] = None,
    changed_fields: Optional[list] = None,
) -> bool:
    """发布用户资料更新事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = UserEvent(
        event_type=UserEventTypesExt.PROFILE_UPDATED,
        user_id=user_id,
        payload={
            "nickname": nickname,
            "avatar": avatar,
            "changed_fields": changed_fields or [],
        },
        source="user-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id=user_id)
        logger.info(f"Published user.profile.updated event for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish profile_updated event: {e}")
        return False


async def publish_membership_upgraded(
    user_id: str,
    old_level: str,
    new_level: str,
    expire_at: Optional[str] = None,
) -> bool:
    """发布会员升级事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = UserEvent(
        event_type=UserEventTypesExt.MEMBERSHIP_UPGRADED,
        user_id=user_id,
        payload={
            "old_level": old_level,
            "new_level": new_level,
            "expire_at": expire_at,
        },
        source="user-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id=user_id)
        logger.info(f"Published user.membership.upgraded event for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish membership_upgraded event: {e}")
        return False


async def publish_membership_expired(
    user_id: str,
    expired_level: str,
) -> bool:
    """发布会员过期事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = UserEvent(
        event_type=UserEventTypesExt.MEMBERSHIP_EXPIRED,
        user_id=user_id,
        payload={
            "expired_level": expired_level,
        },
        source="user-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id=user_id)
        logger.info(f"Published user.membership.expired event for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish membership_expired event: {e}")
        return False


async def publish_account_deleted(
    user_id: str,
    deleted_by: Optional[str] = None,
) -> bool:
    """发布账号删除事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = UserEvent(
        event_type=UserEventTypesExt.ACCOUNT_DELETED,
        user_id=user_id,
        payload={
            "deleted_by": deleted_by,
        },
        source="user-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id=user_id)
        logger.info(f"Published user.account.deleted event for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish account_deleted event: {e}")
        return False


async def publish_account_banned(
    user_id: str,
    reason: Optional[str] = None,
    banned_by: Optional[str] = None,
) -> bool:
    """发布账号封禁事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = UserEvent(
        event_type=UserEventTypesExt.ACCOUNT_BANNED,
        user_id=user_id,
        payload={
            "reason": reason,
            "banned_by": banned_by,
        },
        source="user-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id=user_id)
        logger.info(f"Published user.account.banned event for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish account_banned event: {e}")
        return False


async def publish_role_changed(
    user_id: str,
    old_role: str,
    new_role: str,
    changed_by: Optional[str] = None,
) -> bool:
    """发布角色变更事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = UserEvent(
        event_type=UserEventTypesExt.ROLE_CHANGED,
        user_id=user_id,
        payload={
            "old_role": old_role,
            "new_role": new_role,
            "changed_by": changed_by,
        },
        source="user-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id=user_id)
        logger.info(f"Published user.role.changed event for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish role_changed event: {e}")
        return False


async def publish_lawyer_verified(
    user_id: str,
    is_verified: bool = True,
    firm_name: Optional[str] = None,
) -> bool:
    """发布律师认证事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = UserEvent(
        event_type=UserEventTypesExt.LAWYER_VERIFIED,
        user_id=user_id,
        payload={
            "is_verified": is_verified,
            "firm_name": firm_name,
        },
        source="user-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id=user_id)
        logger.info(f"Published user.lawyer.verified event for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish lawyer_verified event: {e}")
        return False
