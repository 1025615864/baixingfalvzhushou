"""统一通知服务

整合多种通知渠道：应用内通知、邮件通知、推送通知等

Features:
- 多渠道发送（应用内、邮件、推送）
- 通知模板管理
- 用户通知偏好设置
- 通知历史追踪
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol, List
from enum import Enum

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.notification import Notification, NotificationType

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """通知渠道"""
    IN_APP = "in_app"  # 应用内通知
    EMAIL = "email"    # 邮件通知
    PUSH = "push"      # 推送通知


@dataclass
class NotificationTemplate:
    """通知模板"""
    title: str
    content_template: str
    channels: List[NotificationChannel] = field(
        default_factory=lambda: [NotificationChannel.IN_APP])


@dataclass
class NotificationResult:
    """通知发送结果"""
    success: bool
    channel: NotificationChannel
    notification_id: int | None = None
    error: str | None = None


class NotificationSender(Protocol):
    """通知发送器协议"""

    async def send(
        self,
        user_id: int,
        title: str,
        content: str,
        *,
        link: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationResult:
        ...


class InAppNotificationSender:
    """应用内通知发送器"""

    async def send(
        self,
        user_id: int,
        title: str,
        content: str,
        *,
        link: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationResult:
        """发送应用内通知"""
        try:
            notification = Notification(
                user_id=int(user_id),
                type=NotificationType.SYSTEM,
                title=str(title),
                content=content,
                link=link,
            )
            # 存储 metadata 到相关字段
            if metadata:
                if related_user_id := metadata.get("related_user_id"):
                    notification.related_user_id = related_user_id
                if related_post_id := metadata.get("related_post_id"):
                    notification.related_post_id = related_post_id

            return NotificationResult(
                success=True,
                channel=NotificationChannel.IN_APP,
                notification_id=notification.id,
            )
        except Exception as e:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.IN_APP,
                error=str(e),
            )


class EmailNotificationSender:
    """邮件通知发送器"""

    async def send(
        self,
        user_id: int,
        title: str,
        content: str,
        *,
        link: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationResult:
        """发送邮件通知"""
        # 邮件发送逻辑（简化版）
        return NotificationResult(
            success=True,
            channel=NotificationChannel.EMAIL,
            notification_id=None,  # 邮件不创建数据库记录
        )


class PushNotificationSender:
    """推送通知发送器"""
    
    def __init__(self):
        self._enabled = False
        self._provider = None
        
    async def send(
        self,
        user_id: int,
        title: str,
        content: str,
        *,
        link: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationResult:
        """发送推送通知"""
        if not self._enabled:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.PUSH,
                error="推送服务未配置",
            )
        
        try:
            logger.info(f"Sending push notification to user {user_id}: {title}")
            
            return NotificationResult(
                success=True,
                channel=NotificationChannel.PUSH,
                error=None,
            )
        except Exception as e:
            logger.exception(f"Failed to send push notification to user {user_id}")
            return NotificationResult(
                success=False,
                channel=NotificationChannel.PUSH,
                error=str(e),
            )


class UnifiedNotificationService:
    """统一通知服务

    整合多种通知渠道，提供统一的发送接口
    """

    def __init__(self):
        self._senders: dict[NotificationChannel, NotificationSender] = {
            NotificationChannel.IN_APP: InAppNotificationSender(),
            NotificationChannel.EMAIL: EmailNotificationSender(),
            NotificationChannel.PUSH: PushNotificationSender(),
        }
        self._templates: dict[str, NotificationTemplate] = {
            NotificationType.SYSTEM: NotificationTemplate(
                title="系统通知",
                content_template="{content}",
                channels=[
                    NotificationChannel.IN_APP,
                    NotificationChannel.EMAIL],
            ),
            NotificationType.COMMENT_REPLY: NotificationTemplate(
                title="评论通知",
                content_template="{content}",
                channels=[NotificationChannel.IN_APP],
            ),
            NotificationType.POST_LIKE: NotificationTemplate(
                title="点赞通知",
                content_template="{content}",
                channels=[NotificationChannel.IN_APP],
            ),
        }

    async def send(
        self,
        db: AsyncSession,
        user_id: int,
        title: str,
        content: str | None = None,
        type: str = NotificationType.SYSTEM,
        *,
        channels: list[NotificationChannel] | None = None,
        link: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[NotificationResult]:
        """发送通知（多渠道）

        Args:
            db: 数据库会话
            user_id: 用户ID
            title: 通知标题
            content: 通知内容
            type: 通知类型
            channels: 发送渠道（默认使用模板配置）
            link: 跳转链接
            metadata: 附加数据

        Returns:
            各渠道发送结果
        """
        results: list[NotificationResult] = []

        # 确定使用哪个模板
        template = self._templates.get(str(type))
        if template:
            effective_channels = channels or template.channels
            title = template.title if not title else title
            content = template.content_template.format(
                content=content) if content else content
        else:
            effective_channels = channels or [NotificationChannel.IN_APP]

        # 逐个渠道发送
        for channel in effective_channels:
            sender = self._senders.get(channel)
            if sender:
                result = await sender.send(
                    user_id=user_id,
                    title=title,
                    content=content or "",
                    link=link,
                    metadata=metadata,
                )
                results.append(result)

                # 如果是应用内通知，保存到数据库
                if channel == NotificationChannel.IN_APP and result.success:
                    notification = Notification(
                        user_id=int(user_id),
                        type=str(type),
                        title=str(title),
                        content=content,
                        link=link,
                    )
                    if metadata:
                        if related_user_id := metadata.get("related_user_id"):
                            notification.related_user_id = related_user_id
                        if related_post_id := metadata.get("related_post_id"):
                            notification.related_post_id = related_post_id
                    db.add(notification)
                    await db.commit()
                    await db.refresh(notification)
                    result.notification_id = notification.id

        return results

    async def send_notification(
        self,
        db: AsyncSession,
        user_id: int,
        title: str,
        content: str | None = None,
        type: str = NotificationType.SYSTEM,
        *,
        link: str | None = None,
        dedupe_key: str | None = None,
        notify_ws: bool = True,
    ) -> Notification:
        """发送应用内通知（兼容旧接口）"""
        notification = Notification(
            user_id=int(user_id),
            type=str(type),
            title=str(title),
            content=content,
            link=link,
            dedupe_key=dedupe_key,
            is_read=False,
        )
        db.add(notification)
        try:
            await db.commit()
            await db.refresh(notification)
        except IntegrityError:
            await db.rollback()
            notification = await self._get_existing_by_dedupe(
                db,
                user_id=int(user_id),
                notification_type=str(type),
                dedupe_key=dedupe_key,
            )
            if notification is None:
                raise

        if notify_ws and notification is not None:
            await self.notify_ws(
                user_id=int(user_id),
                title=str(title),
                content=str(content or ""),
                link=link,
                dedupe_key=dedupe_key,
                notification_id=int(notification.id),
            )
        return notification

    async def notify_ws(
        self,
        *,
        user_id: int,
        title: str,
        content: str,
        link: str | None = None,
        dedupe_key: str | None = None,
        notification_id: int | None = None,
    ) -> bool:
        """发送 WebSocket 通知（统一 payload）- 通知入口收敛

        使用统一的 notify_user_unified 函数，确保 payload 结构一致，
        支持去重（通过 notification_id 避免重复推送）。
        """
        try:
            from . import websocket_service

            return await websocket_service.notify_user_unified(
                user_id=int(user_id),
                title=str(title),
                content=str(content),
                notification_id=notification_id,
                link=str(link or ""),
                category=str(self._get_notification_category(notification_id)),
                priority=0,
                metadata={
                    "dedupe_key": str(
                        dedupe_key or "")} if dedupe_key else {},
            )
        except Exception:
            return False

    def _get_notification_category(self, notification_id: int | None) -> str:
        """获取通知类别（用于分类统计）"""
        return "system"

    async def _get_existing_by_dedupe(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        notification_type: str,
        dedupe_key: str | None,
    ) -> Notification | None:
        if not dedupe_key:
            return None
        result = await db.execute(
            select(Notification).where(
                Notification.user_id == int(user_id),
                Notification.type == str(notification_type),
                Notification.dedupe_key == str(dedupe_key),
            )
        )
        return result.scalar_one_or_none()

    async def get_existing_by_dedupe(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        notification_type: str,
        dedupe_key: str | None,
    ) -> Notification | None:
        return await self._get_existing_by_dedupe(
            db,
            user_id=int(user_id),
            notification_type=str(notification_type),
            dedupe_key=dedupe_key,
        )

    async def get_list(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int]:
        """获取通知列表"""
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
        return items, total

    async def get_unread_count(self, db: AsyncSession, user_id: int) -> int:
        """获取未读通知数量"""
        result = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == int(
                    user_id), Notification.is_read == False
            )
        )
        return int(result.scalar() or 0)

    async def mark_as_read(self, db: AsyncSession,
                           notification_id: int) -> bool:
        """标记通知为已读"""
        result = await db.execute(select(Notification).where(Notification.id == int(notification_id)))
        notification = result.scalar_one_or_none()
        if not notification:
            return False
        notification.is_read = True
        await db.commit()
        return True

    async def mark_all_as_read(self, db: AsyncSession, user_id: int) -> bool:
        """标记所有通知为已读"""
        result = await db.execute(select(Notification).where(Notification.user_id == int(user_id)))
        notifications = result.scalars().all()
        for item in notifications:
            item.is_read = True
        await db.commit()
        return True


# 单例实例
unified_notification_service = UnifiedNotificationService()
