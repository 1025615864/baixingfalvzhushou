from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Any

from fastapi import HTTPException
from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.notification import Notification


class NotificationService:

    def __init__(self, db: AsyncSession, user: Optional[Any] = None):
        self.db = db
        self.user = user

    async def get_notifications(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
    ) -> dict:
        stmt = select(Notification).where(Notification.user_id == user_id)
        count_stmt = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)

        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
            count_stmt = count_stmt.where(Notification.is_read == False)
        if notification_type:
            stmt = stmt.where(Notification.type == notification_type)
            count_stmt = count_stmt.where(Notification.type == notification_type)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.order_by(Notification.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return {
            "items": [self._to_dict(n) for n in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_unread_count(self, user_id: int) -> int:
        stmt = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def mark_as_read(self, user_id: int, notification_id: int) -> dict:
        try:
            stmt = select(Notification).where(Notification.id == notification_id)
            result = await self.db.execute(stmt)
            notification = result.scalar_one_or_none()

            if notification is None:
                raise HTTPException(status_code=404, detail="通知不存在")
            if notification.user_id != user_id:
                raise HTTPException(status_code=403, detail="无权操作此通知")

            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await self.db.commit()
            return {"message": "已标记为已读"}
        except HTTPException:
            raise
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def mark_all_as_read(self, user_id: int) -> dict:
        try:
            stmt = (
                update(Notification)
                .where(Notification.user_id == user_id, Notification.is_read == False)
                .values(is_read=True, read_at=datetime.now(timezone.utc))
            )
            await self.db.execute(stmt)
            await self.db.commit()
            return {"message": "全部标记为已读"}
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def delete_notification(self, user_id: int, notification_id: int) -> dict:
        try:
            stmt = select(Notification).where(Notification.id == notification_id)
            result = await self.db.execute(stmt)
            notification = result.scalar_one_or_none()

            if notification is None:
                raise HTTPException(status_code=404, detail="通知不存在")
            if notification.user_id != user_id:
                raise HTTPException(status_code=403, detail="无权操作此通知")

            await self.db.delete(notification)
            await self.db.commit()
            return {"message": "已删除"}
        except HTTPException:
            raise
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def batch_mark_read(self, user_id: int, ids: list[int]) -> dict:
        try:
            stmt = (
                update(Notification)
                .where(
                    Notification.user_id == user_id,
                    Notification.id.in_(ids),
                    Notification.is_read == False,
                )
                .values(is_read=True, read_at=datetime.now(timezone.utc))
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            success_count = result.rowcount
            return {
                "success_count": success_count,
                "failed_count": len(ids) - success_count,
                "message": f"已标记{success_count}条为已读",
            }
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def batch_delete(self, user_id: int, ids: list[int]) -> dict:
        try:
            stmt = (
                delete(Notification)
                .where(
                    Notification.user_id == user_id,
                    Notification.id.in_(ids),
                )
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            success_count = result.rowcount
            return {
                "success_count": success_count,
                "failed_count": len(ids) - success_count,
                "message": f"已删除{success_count}条",
            }
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def get_notification_types(self, user_id: int) -> dict:
        stmt = (
            select(Notification.type, func.count().label("count"))
            .where(Notification.user_id == user_id)
            .group_by(Notification.type)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        types = {row.type: row.count for row in rows}
        return {"types": types}

    async def get_system_notifications(
        self,
        page: int = 1,
        page_size: int = 20,
        is_published: Optional[bool] = None,
        keyword: Optional[str] = None,
    ) -> dict:
        page_size = min(page_size, 100)
        stmt = select(Notification).where(Notification.type == "system")
        count_stmt = select(func.count()).select_from(Notification).where(Notification.type == "system")

        if is_published is not None:
            stmt = stmt.where(Notification.is_read == is_published)
            count_stmt = count_stmt.where(Notification.is_read == is_published)
        if keyword:
            stmt = stmt.where(Notification.title.ilike(f"%{keyword}%"))
            count_stmt = count_stmt.where(Notification.title.ilike(f"%{keyword}%"))

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.order_by(Notification.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return {
            "items": [self._to_system_dict(n) for n in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def create_system_notification(self, data: dict) -> dict:
        try:
            notification = Notification(
                user_id=data.get("user_id", 1),
                type="system",
                title=data["title"],
                content=data.get("content"),
                link=data.get("link"),
            )
            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)
            return self._to_system_dict(notification)
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def update_system_notification(self, notification_id: int, data: dict) -> dict:
        try:
            stmt = select(Notification).where(Notification.id == notification_id, Notification.type == "system")
            result = await self.db.execute(stmt)
            notification = result.scalar_one_or_none()

            if notification is None:
                raise HTTPException(status_code=404, detail="系统通知不存在")

            for field, value in data.items():
                if value is not None and hasattr(notification, field):
                    setattr(notification, field, value)

            await self.db.commit()
            await self.db.refresh(notification)
            return self._to_system_dict(notification)
        except HTTPException:
            raise
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def delete_system_notification(self, notification_id: int) -> dict:
        try:
            stmt = select(Notification).where(Notification.id == notification_id, Notification.type == "system")
            result = await self.db.execute(stmt)
            notification = result.scalar_one_or_none()

            if notification is None:
                raise HTTPException(status_code=404, detail="系统通知不存在")

            await self.db.delete(notification)
            await self.db.commit()
            return {"message": "已删除"}
        except HTTPException:
            raise
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    def _to_dict(self, notification: Notification) -> dict:
        return {
            "id": notification.id,
            "user_id": notification.user_id,
            "notification_type": notification.type,
            "title": notification.title,
            "content": notification.content,
            "link": notification.link,
            "is_read": notification.is_read,
            "read_at": notification.read_at.isoformat() if notification.read_at else None,
            "related_user_id": notification.related_user_id,
            "related_post_id": notification.related_post_id,
            "related_comment_id": notification.related_comment_id,
            "created_at": notification.created_at.isoformat() if notification.created_at else None,
        }

    def _to_system_dict(self, notification: Notification) -> dict:
        return {
            "id": notification.id,
            "title": notification.title,
            "content": notification.content,
            "target_type": "all",
            "target_ids": None,
            "sent_count": 0,
            "read_count": 0,
            "is_published": not notification.is_read,
            "published_at": notification.read_at.isoformat() if notification.read_at else None,
            "expires_at": None,
            "created_by": "admin",
            "created_at": notification.created_at.isoformat() if notification.created_at else None,
            "updated_at": notification.created_at.isoformat() if notification.created_at else None,
        }
