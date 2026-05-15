from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.feedback import FeedbackTicket


class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_feedback(
        self, user_id: int, subject: str, content: str
    ) -> FeedbackTicket:
        try:
            ticket = FeedbackTicket(
                user_id=user_id,
                subject=subject,
                content=content,
                status="open",
            )
            self.db.add(ticket)
            await self.db.commit()
            await self.db.refresh(ticket)
            return ticket
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def get_feedback_list(
        self, user_id: int, page: int, page_size: int
    ) -> dict[str, Any]:
        conditions = [FeedbackTicket.user_id == user_id]
        count_stmt = select(func.count()).select_from(FeedbackTicket).where(*conditions)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(FeedbackTicket)
            .where(*conditions)
            .order_by(FeedbackTicket.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return {
            "items": [self._ticket_to_dict(t) for t in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_feedback_stats(self) -> dict[str, Any]:
        total_stmt = select(func.count()).select_from(FeedbackTicket)
        total = (await self.db.execute(total_stmt)).scalar() or 0

        status_stmt = (
            select(FeedbackTicket.status, func.count())
            .group_by(FeedbackTicket.status)
        )
        status_result = await self.db.execute(status_stmt)
        status_counts = dict(status_result.all())

        unassigned_stmt = select(func.count()).select_from(FeedbackTicket).where(
            FeedbackTicket.status == "open",
            FeedbackTicket.admin_id.is_(None),
        )
        unassigned = (await self.db.execute(unassigned_stmt)).scalar() or 0

        avg_response_stmt = select(
            func.avg(
                func.extract("epoch", FeedbackTicket.updated_at - FeedbackTicket.created_at)
            )
        ).where(
            FeedbackTicket.admin_reply.isnot(None),
        )
        avg_response_seconds = (await self.db.execute(avg_response_stmt)).scalar()

        avg_response_hours = None
        if avg_response_seconds is not None:
            avg_response_hours = round(float(avg_response_seconds) / 3600, 2)

        return {
            "total": total,
            "open": status_counts.get("open", 0),
            "processing": status_counts.get("processing", 0),
            "closed": status_counts.get("closed", 0),
            "unassigned": unassigned,
            "avg_response_hours": avg_response_hours,
        }

    async def get_admin_feedback_list(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
        keyword: str | None = None,
    ) -> dict[str, Any]:
        page_size = min(page_size, 100)
        conditions = []
        if status:
            conditions.append(FeedbackTicket.status == status)
        if keyword:
            conditions.append(
                FeedbackTicket.subject.ilike(f"%{keyword}%")
                | FeedbackTicket.content.ilike(f"%{keyword}%")
            )

        count_stmt = select(func.count()).select_from(FeedbackTicket).where(*conditions)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(FeedbackTicket)
            .where(*conditions)
            .order_by(FeedbackTicket.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return {
            "items": [self._ticket_to_dict(t) for t in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def update_feedback(
        self, ticket_id: int, data: dict[str, Any]
    ) -> FeedbackTicket:
        try:
            ticket = await self.db.get(FeedbackTicket, ticket_id)
            if ticket is None:
                raise HTTPException(status_code=404, detail="反馈记录不存在")

            for field, value in data.items():
                if value is not None and hasattr(ticket, field):
                    setattr(ticket, field, value)

            await self.db.commit()
            await self.db.refresh(ticket)
            return ticket
        except HTTPException:
            raise
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    @staticmethod
    def _ticket_to_dict(ticket: FeedbackTicket) -> dict[str, Any]:
        return {
            "id": ticket.id,
            "user_id": ticket.user_id,
            "subject": ticket.subject,
            "content": ticket.content,
            "status": ticket.status,
            "admin_reply": ticket.admin_reply,
            "admin_id": ticket.admin_id,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        }
