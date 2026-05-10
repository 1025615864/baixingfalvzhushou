"""Unified notification service."""
from __future__ import annotations
import enum
import time
from typing import Optional, Any
from dataclasses import dataclass, field


class NotificationChannel(enum.Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    WECHAT = "wechat"
    PUSH = "push"


class NotificationCategory(enum.Enum):
    SYSTEM = "system"
    CONSULTATION = "consultation"
    PAYMENT = "payment"
    REMINDER = "reminder"
    MARKETING = "marketing"


@dataclass
class NotificationResult:
    success: bool
    channel: NotificationChannel
    notification_id: Optional[int] = None
    error: Optional[str] = None


@dataclass
class NotificationTemplate:
    title: str
    content_template: str
    channels: list[NotificationChannel] = field(default_factory=lambda: [NotificationChannel.IN_APP])


class InAppNotificationSender:
    def __init__(self):
        self._notifications: list[dict] = []
        self._next_id = 1

    async def send(self, user_id: int, title: str, content: str, **kwargs) -> NotificationResult:
        notif_id = self._next_id
        self._next_id += 1
        self._notifications.append({
            "id": notif_id,
            "user_id": user_id,
            "title": title,
            "content": content,
        })
        return NotificationResult(
            success=True,
            channel=NotificationChannel.IN_APP,
            notification_id=notif_id,
        )


class EmailNotificationSender:
    def __init__(self):
        self._sent: list[dict] = []

    async def send(self, user_id: int, title: str, content: str, **kwargs) -> NotificationResult:
        self._sent.append({
            "user_id": user_id,
            "title": title,
            "content": content,
        })
        return NotificationResult(
            success=True,
            channel=NotificationChannel.EMAIL,
            notification_id=None,
        )


class PushNotificationSender:
    def __init__(self):
        self._sent: list[dict] = []

    async def send(self, user_id: int, title: str, content: str, **kwargs) -> NotificationResult:
        self._sent.append({
            "user_id": user_id,
            "title": title,
            "content": content,
        })
        return NotificationResult(
            success=True,
            channel=NotificationChannel.PUSH,
            notification_id=None,
        )


@dataclass
class UnifiedNotification:
    id: str
    user_id: int
    title: str
    content: str
    channel: NotificationChannel = NotificationChannel.IN_APP
    category: NotificationCategory = NotificationCategory.SYSTEM
    priority: int = 0
    read: bool = False
    sent: bool = False
    created_at: float = field(default_factory=time.time)
    sent_at: Optional[float] = None


class UnifiedNotificationService:
    def __init__(self):
        self._notifications: dict[str, UnifiedNotification] = {}
        self._next_id = 1
        self._preferences: dict[int, dict] = {}
        self._senders: dict[NotificationChannel, Any] = {
            NotificationChannel.IN_APP: InAppNotificationSender(),
            NotificationChannel.EMAIL: EmailNotificationSender(),
            NotificationChannel.PUSH: PushNotificationSender(),
        }
        self._templates: dict[Any, NotificationTemplate] = {}
        self._init_default_templates()

    def _init_default_templates(self) -> None:
        try:
            from app.models.notification import NotificationType
            self._templates[NotificationType.SYSTEM] = NotificationTemplate(
                title="系统通知",
                content_template="{content}",
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            )
            self._templates[NotificationType.COMMENT_REPLY] = NotificationTemplate(
                title="评论回复",
                content_template="{content}",
                channels=[NotificationChannel.IN_APP],
            )
            self._templates[NotificationType.POST_LIKE] = NotificationTemplate(
                title="帖子点赞",
                content_template="{content}",
                channels=[NotificationChannel.IN_APP],
            )
        except (ImportError, AttributeError):
            pass

    async def send(self, db, user_id: int, title: str, content: str, type: Any = None, channels: Optional[list[NotificationChannel]] = None, metadata: Optional[dict] = None, link: Optional[str] = None) -> list[NotificationResult]:
        if channels is None:
            template = self._templates.get(type) if type else None
            if template:
                channels = template.channels
            else:
                channels = [NotificationChannel.IN_APP]
        if not channels:
            template = self._templates.get(type) if type else None
            if template:
                channels = template.channels
            else:
                channels = [NotificationChannel.IN_APP]
        results = []
        for channel in channels:
            sender = self._senders.get(channel)
            if sender:
                try:
                    result = await sender.send(user_id=user_id, title=title, content=content or "")
                    results.append(result)
                except Exception as e:
                    results.append(NotificationResult(success=False, channel=channel, error=str(e)))
        return results

    async def send_notification(self, user_id: int, title: str, content: str, channel: NotificationChannel = NotificationChannel.IN_APP, category: NotificationCategory = NotificationCategory.SYSTEM, priority: int = 0) -> UnifiedNotification:
        notif_id = f"unotif_{self._next_id}"
        self._next_id += 1
        notif = UnifiedNotification(id=notif_id, user_id=user_id, title=title, content=content, channel=channel, category=category, priority=priority, sent=True, sent_at=time.time())
        self._notifications[notif_id] = notif
        return notif

    async def get_notification(self, notification_id: str) -> Optional[UnifiedNotification]:
        return self._notifications.get(notification_id)

    async def get_user_notifications(self, user_id: int, channel: Optional[NotificationChannel] = None, unread_only: bool = False, limit: int = 20) -> list[UnifiedNotification]:
        notifs = [n for n in self._notifications.values() if n.user_id == user_id]
        if channel:
            notifs = [n for n in notifs if n.channel == channel]
        if unread_only:
            notifs = [n for n in notifs if not n.read]
        return notifs[:limit]

    async def mark_as_read(self, notification_id: str) -> dict:
        notif = self._notifications.get(notification_id)
        if not notif:
            return {"success": False, "error": "通知不存在"}
        notif.read = True
        return {"success": True}

    async def mark_all_read(self, user_id: int) -> dict:
        count = 0
        for n in self._notifications.values():
            if n.user_id == user_id and not n.read:
                n.read = True
                count += 1
        return {"success": True, "marked_count": count}

    async def delete_notification(self, notification_id: str) -> dict:
        if notification_id not in self._notifications:
            return {"success": False, "error": "通知不存在"}
        del self._notifications[notification_id]
        return {"success": True}

    async def get_unread_count(self, user_id: int) -> int:
        return sum(1 for n in self._notifications.values() if n.user_id == user_id and not n.read)

    async def set_preference(self, user_id: int, channel: NotificationChannel, enabled: bool) -> dict:
        if user_id not in self._preferences:
            self._preferences[user_id] = {}
        self._preferences[user_id][channel.value] = enabled
        return {"success": True}

    async def get_preferences(self, user_id: int) -> dict:
        return self._preferences.get(user_id, {})

    async def broadcast(self, title: str, content: str, channel: NotificationChannel = NotificationChannel.IN_APP, category: NotificationCategory = NotificationCategory.SYSTEM) -> dict:
        return {"success": True, "sent_count": 0}


unified_notification_service = UnifiedNotificationService()
