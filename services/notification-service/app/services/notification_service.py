"""通知服务 - 服务层"""
from typing import List, Tuple, Optional, Dict
from datetime import datetime

from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, NotificationSettings


class NotificationService:
    """通知服务"""

    async def list_notifications(
        self,
        session: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> Tuple[List[Notification], int, int]:
        """获取用户通知列表"""
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        unread_query = select(func.count()).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        unread_result = await session.execute(unread_query)
        unread_count = unread_result.scalar() or 0

        query = query.order_by(desc(Notification.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await session.execute(query)
        notifications = result.scalars().all()

        return list(notifications), total, unread_count

    async def create_notification(
        self,
        session: AsyncSession,
        user_id: int,
        type: str,
        title: str,
        content: Optional[str] = None,
        sent_at: Optional[datetime] = None,
    ) -> Notification:
        """创建通知"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            content=content,
            is_read=False,
            sent_at=sent_at,
        )
        session.add(notification)
        await session.flush()
        return notification

    async def create_batch_notifications(
        self,
        session: AsyncSession,
        user_ids: List[int],
        type: str,
        title: str,
        content: Optional[str] = None,
    ) -> int:
        """批量创建通知（用于系统通知）"""
        notifications = [
            Notification(
                user_id=uid,
                type=type,
                title=title,
                content=content,
                is_read=False,
            )
            for uid in user_ids
        ]
        session.add_all(notifications)
        await session.flush()
        return len(notifications)

    async def get_notification(
        self,
        session: AsyncSession,
        notification_id: int,
    ) -> Optional[Notification]:
        """获取通知详情"""
        query = select(Notification).where(Notification.id == notification_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def mark_as_read(
        self,
        session: AsyncSession,
        notification_id: int,
    ) -> bool:
        """标记通知为已读"""
        notification = await self.get_notification(session, notification_id)
        if not notification:
            return False

        notification.is_read = True
        await session.flush()
        return True

    async def mark_all_as_read(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> int:
        """标记所有通知为已读"""
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True)
        )
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount

    async def delete_notification(
        self,
        session: AsyncSession,
        notification_id: int,
    ) -> bool:
        """删除通知"""
        notification = await self.get_notification(session, notification_id)
        if not notification:
            return False

        await session.delete(notification)
        await session.flush()
        return True

    async def get_unread_count(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> int:
        """获取用户未读通知数量"""
        query = select(func.count()).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        result = await session.execute(query)
        return result.scalar() or 0

    async def get_settings(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> NotificationSettings:
        """获取通知设置"""
        query = select(NotificationSettings).where(
            NotificationSettings.user_id == user_id
        )
        result = await session.execute(query)
        settings = result.scalar_one_or_none()

        if not settings:
            settings = NotificationSettings(user_id=user_id)
            session.add(settings)
            await session.flush()

        return settings

    async def update_settings(
        self,
        session: AsyncSession,
        user_id: int,
        updates: Dict,
    ) -> NotificationSettings:
        """更新通知设置"""
        settings = await self.get_settings(session, user_id)

        for key, value in updates.items():
            if hasattr(settings, key) and value is not None:
                setattr(settings, key, value)

        await session.flush()
        return settings

    async def should_send_notification(
        self,
        session: AsyncSession,
        user_id: int,
        channel: str,
    ) -> bool:
        """检查是否应该发送通知（考虑用户设置和免打扰时段）"""
        import datetime as dt

        settings = await self.get_settings(session, user_id)

        if channel == "email" and not settings.email_enabled:
            return False
        if channel == "sms" and not settings.sms_enabled:
            return False
        if channel == "push" and not settings.push_enabled:
            return False

        if settings.quiet_hours_start and settings.quiet_hours_end:
            now = dt.datetime.now().time()
            start = dt.time.fromisoformat(settings.quiet_hours_start)
            end = dt.time.fromisoformat(settings.quiet_hours_end)

            if start <= now <= end:
                return False

        return True


notification_service = NotificationService()
