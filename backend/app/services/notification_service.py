"""通知服务

集成熔断器保护，防止通知服务故障导致系统崩溃。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.notification import Notification, NotificationType
from ..utils.circuit_breaker import (
    CircuitBreaker,
    CircuitConfig,
    CircuitBreakerOpen,
    circuit_breaker_registry,
)

logger = logging.getLogger(__name__)

# 通知服务熔断器配置
# 通知服务相对不那么关键，可以设置较宽松的熔断阈值
NOTIFICATION_CIRCUIT_CONFIG = CircuitConfig(
    failure_threshold=5,       # 连续5次失败后打开熔断器
    success_threshold=2,       # 半开状态下需要2次成功才能关闭
    timeout_seconds=30.0,      # 30秒后进入半开状态
    expected_exception=Exception,  # 捕获所有异常
)

# 全局通知服务熔断器
_notification_circuit_breaker: Optional[CircuitBreaker] = None


async def get_notification_circuit_breaker() -> CircuitBreaker:
    """获取通知服务熔断器实例"""
    global _notification_circuit_breaker
    if _notification_circuit_breaker is None:
        _notification_circuit_breaker = await circuit_breaker_registry.get_or_create(
            "notification_service",
            NOTIFICATION_CIRCUIT_CONFIG,
        )
    return _notification_circuit_breaker


@dataclass
class NotificationList:
    items: list[Notification]
    total: int
    page: int
    page_size: int


@dataclass
class NotificationPreferences:
    email_enabled: bool = True
    push_enabled: bool = True


_NOTIFICATION_PREFERENCES: dict[int, NotificationPreferences] = {}


class NotificationService:
    async def send(
        self,
        db: AsyncSession,
        user_id: int,
        title: str,
        content: str | None = None,
        type: str = NotificationType.SYSTEM,
        *,
        link: str | None = None,
        related_user_id: int | None = None,
        related_post_id: int | None = None,
        related_comment_id: int | None = None,
        dedupe_key: str | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=int(user_id),
            type=str(type),
            title=str(title),
            content=content,
            link=link,
            related_user_id=related_user_id,
            related_post_id=related_post_id,
            related_comment_id=related_comment_id,
            dedupe_key=dedupe_key,
            is_read=False,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    async def get_list(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> NotificationList:
        base_query = select(Notification).where(
            Notification.user_id == int(user_id))
        total = int(
            (await db.execute(select(func.count(Notification.id)).where(Notification.user_id == int(user_id))))
            .scalar()
            or 0
        )
        result = await db.execute(
            base_query.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        return NotificationList(items=items, total=total,
                                page=page, page_size=page_size)

    async def get_unread_count(self, db: AsyncSession, user_id: int) -> int:
        result = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == int(
                    user_id), Notification.is_read == False
            )
        )
        return int(result.scalar() or 0)

    async def mark_as_read(self, db: AsyncSession,
                           notification_id: int) -> bool:
        result = await db.execute(select(Notification).where(Notification.id == int(notification_id)))
        notification = result.scalar_one_or_none()
        if not notification:
            return False
        notification.is_read = True
        await db.commit()
        return True

    async def mark_all_as_read(self, db: AsyncSession, user_id: int) -> bool:
        result = await db.execute(select(Notification).where(Notification.user_id == int(user_id)))
        notifications = result.scalars().all()
        for item in notifications:
            item.is_read = True
        await db.commit()
        return True

    async def delete(self, db: AsyncSession, notification_id: int) -> bool:
        result = await db.execute(select(Notification).where(Notification.id == int(notification_id)))
        notification = result.scalar_one_or_none()
        if not notification:
            return False
        await db.delete(notification)
        await db.commit()
        return True

    async def get_by_type(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        notification_type: str,
    ) -> list[Notification]:
        result = await db.execute(
            select(Notification)
            .where(
                Notification.user_id == int(user_id),
                Notification.type == str(notification_type),
            )
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_preferences(
            self, db: AsyncSession, user_id: int) -> NotificationPreferences:
        return _NOTIFICATION_PREFERENCES.get(
            int(user_id), NotificationPreferences())

    async def update_preferences(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        email_enabled: bool | None = None,
        push_enabled: bool | None = None,
    ) -> bool:
        preferences = _NOTIFICATION_PREFERENCES.get(
            int(user_id), NotificationPreferences())
        if email_enabled is not None:
            preferences.email_enabled = bool(email_enabled)
        if push_enabled is not None:
            preferences.push_enabled = bool(push_enabled)
        _NOTIFICATION_PREFERENCES[int(user_id)] = preferences
        return True

    def get_template(self, template_type: str) -> dict[str, Any] | None:
        templates = {
            "system": {"title": "系统通知", "content": "{content}"},
            "comment": {"title": "评论通知", "content": "{content}"},
            "post": {"title": "帖子通知", "content": "{content}"},
        }
        return templates.get(str(template_type))


notification_service = NotificationService()
