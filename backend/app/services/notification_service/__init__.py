"""Notification service."""
from __future__ import annotations
import time
import enum
from typing import Optional, Any
from dataclasses import dataclass, field


class NotificationType(enum.Enum):
    SYSTEM = "system"
    CONSULTATION = "consultation"
    REMINDER = "reminder"
    MARKETING = "marketing"


class NotificationPriority(enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    id: int
    user_id: int = 0
    title: str = ""
    content: str = ""
    type: Any = NotificationType.SYSTEM
    priority: NotificationPriority = NotificationPriority.NORMAL
    is_read: bool = False
    created_at: float = field(default_factory=time.time)


@dataclass
class NotificationList:
    items: list[Notification] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


@dataclass
class NotificationPreferences:
    email_enabled: bool = True
    push_enabled: bool = True


class NotificationService:
    def __init__(self):
        self._notifications: dict[str, Notification] = {}
        self._next_id = 1
        self._preferences: dict[int, NotificationPreferences] = {}
        self._templates: dict[str, dict] = {
            "system": {"title": "系统通知", "content": "{content}"},
            "consultation": {"title": "咨询通知", "content": "{content}"},
            "reminder": {"title": "提醒通知", "content": "{content}"},
        }

    async def create_notification(self, user_id: int, title: str, content: str, notification_type: NotificationType = NotificationType.SYSTEM, priority: NotificationPriority = NotificationPriority.NORMAL) -> Notification:
        notif_id = f"notif_{self._next_id}"
        self._next_id += 1
        notif = Notification(id=self._next_id - 1, user_id=user_id, title=title, content=content, type=notification_type, priority=priority)
        self._notifications[notif_id] = notif
        return notif

    async def send(self, db, user_id: int, title: str, content: str, type: NotificationType = NotificationType.SYSTEM, **kwargs) -> Notification:
        notif = Notification(id=self._next_id, user_id=user_id, title=title, content=content, type=type)
        self._next_id += 1
        if db is not None:
            db.add(notif)
            await db.commit()
            await db.refresh(notif)
        return notif

    async def get_notification(self, notification_id: str) -> Optional[Notification]:
        return self._notifications.get(notification_id)

    async def get_list(self, db, user_id: int, page: int = 1, page_size: int = 20) -> NotificationList:
        notifs = [n for n in self._notifications.values() if n.user_id == user_id]
        total = len(notifs)
        start = (page - 1) * page_size
        items = notifs[start:start + page_size]
        return NotificationList(items=items, total=total, page=page, page_size=page_size)

    async def get_user_notifications(self, user_id: int, unread_only: bool = False, limit: int = 20) -> list[Notification]:
        notifs = [n for n in self._notifications.values() if n.user_id == user_id]
        if unread_only:
            notifs = [n for n in notifs if not n.is_read]
        return notifs[:limit]

    async def get_unread_count(self, db, user_id: int) -> int:
        return sum(1 for n in self._notifications.values() if n.user_id == user_id and not n.is_read)

    async def mark_as_read(self, db, notification_id: int) -> bool:
        for n in self._notifications.values():
            if n.id == notification_id:
                n.is_read = True
                if db is not None:
                    await db.commit()
                return True
        return False

    async def mark_all_read(self, user_id: int) -> dict:
        count = 0
        for n in self._notifications.values():
            if n.user_id == user_id and not n.is_read:
                n.is_read = True
                count += 1
        return {"success": True, "marked_count": count}

    async def mark_all_as_read(self, db, user_id: int) -> bool:
        for n in self._notifications.values():
            if n.user_id == user_id and not n.is_read:
                n.is_read = True
        if db is not None:
            await db.commit()
        return True

    async def delete(self, db, notification_id: int) -> bool:
        for key, n in list(self._notifications.items()):
            if n.id == notification_id:
                del self._notifications[key]
                if db is not None:
                    await db.delete(n)
                    await db.commit()
                return True
        return False

    async def delete_notification(self, notification_id: str) -> dict:
        if notification_id not in self._notifications:
            return {"success": False, "error": "通知不存在"}
        del self._notifications[notification_id]
        return {"success": True}

    async def get_by_type(self, db, user_id: int, notification_type: NotificationType = NotificationType.SYSTEM) -> list[Notification]:
        return [n for n in self._notifications.values() if n.user_id == user_id and n.type == notification_type]

    async def get_user_preferences(self, db, user_id: int) -> NotificationPreferences:
        if user_id not in self._preferences:
            self._preferences[user_id] = NotificationPreferences()
        return self._preferences[user_id]

    async def update_preferences(self, db, user_id: int, **kwargs) -> bool:
        if user_id not in self._preferences:
            self._preferences[user_id] = NotificationPreferences()
        prefs = self._preferences[user_id]
        if "email_enabled" in kwargs:
            prefs.email_enabled = kwargs["email_enabled"]
        if "push_enabled" in kwargs:
            prefs.push_enabled = kwargs["push_enabled"]
        return True

    def get_template(self, template_type: str) -> Optional[dict]:
        return self._templates.get(template_type)


notification_service = NotificationService()
