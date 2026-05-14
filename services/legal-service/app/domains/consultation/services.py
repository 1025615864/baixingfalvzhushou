"""咨询领域服务"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ...models import Consultation, ChatMessage
from ...shared.consultation_state_machine import (
    ConsultationStatus,
    ConsultationStateMachine,
)
from ...shared.state_machines import TransitionError

MAX_MESSAGES_PER_CONSULTATION = 200


class ConsultationDomainService:
    """咨询领域服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        category: str,
        title: str,
        description: str,
        ai_assisted: bool = True,
    ) -> Consultation:
        consultation = Consultation(
            user_id=user_id,
            category=category,
            title=title,
            description=description,
            ai_assisted=ai_assisted,
            status="pending",
        )
        self.db.add(consultation)
        await self.db.commit()
        await self.db.refresh(consultation)

        from ...events.producer import event_bus
        await event_bus.publish_consultation_created(consultation)

        return consultation

    async def get(self, consultation_id: int) -> Optional[Consultation]:
        result = await self.db.execute(
            select(Consultation).where(Consultation.id == consultation_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Consultation], int]:
        query = select(Consultation).where(Consultation.user_id == user_id)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Consultation.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        consultations = result.scalars().all()

        return list(consultations), total

    async def update_status(
        self,
        consultation_id: int,
        new_status: str,
    ) -> Optional[Consultation]:
        consultation = await self.get(consultation_id)
        if not consultation:
            return None

        if not ConsultationStateMachine.can_transition_from(consultation.status, new_status):
            raise TransitionError(
                current_state=consultation.status,
                target_state=new_status,
                message=f"不允许的状态转换: {consultation.status} -> {new_status}"
            )

        consultation.status = new_status
        consultation.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(consultation)
        return consultation

    async def assign_lawyer(
        self,
        consultation_id: int,
        lawyer_id: int,
    ) -> Optional[Consultation]:
        consultation = await self.get(consultation_id)
        if not consultation:
            return None

        consultation.lawyer_id = lawyer_id
        consultation.status = "processing"
        consultation.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(consultation)
        return consultation

    async def get_messages(
        self,
        consultation_id: int,
        cursor: Optional[int] = None,
        limit: int = 50,
    ) -> List[ChatMessage]:
        query = select(ChatMessage).where(
            ChatMessage.consultation_id == consultation_id
        )

        if cursor:
            query = query.where(ChatMessage.id > cursor)

        query = query.order_by(ChatMessage.id.asc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_message(
        self,
        consultation_id: int,
        role: str,
        content: str,
    ) -> ChatMessage:
        count_result = await self.db.execute(
            select(func.count()).select_from(ChatMessage).where(
                ChatMessage.consultation_id == consultation_id
            )
        )
        count = count_result.scalar() or 0

        if count >= MAX_MESSAGES_PER_CONSULTATION:
            from ...errors import LegalException, LegalErrorCode
            raise LegalException(
                code=LegalErrorCode.CONSULTATION_LIMIT_EXCEEDED,
                message=f"该咨询消息数已达上限（{MAX_MESSAGES_PER_CONSULTATION}条）"
            )

        message = ChatMessage(
            consultation_id=consultation_id,
            role=role,
            content=content,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def complete(self, consultation_id: int) -> Optional[Consultation]:
        consultation = await self.get(consultation_id)
        if not consultation:
            return None

        if not ConsultationStateMachine.can_transition_from(
            consultation.status, ConsultationStatus.ANSWERED.value
        ):
            raise TransitionError(
                current_state=consultation.status,
                target_state=ConsultationStatus.ANSWERED.value,
            )

        consultation.status = ConsultationStatus.ANSWERED.value
        consultation.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(consultation)

        from ...events.producer import event_bus
        await event_bus.publish_consultation_completed(consultation)

        return consultation

    async def cancel(self, consultation_id: int) -> Optional[Consultation]:
        consultation = await self.get(consultation_id)
        if not consultation:
            return None

        if not ConsultationStateMachine.can_transition_from(
            consultation.status, ConsultationStatus.CANCELLED.value
        ):
            raise TransitionError(
                current_state=consultation.status,
                target_state=ConsultationStatus.CANCELLED.value,
            )

        consultation.status = ConsultationStatus.CANCELLED.value
        consultation.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(consultation)

        from ...events.producer import event_bus
        await event_bus.publish_consultation_cancelled(consultation)

        return consultation

    async def list_pending(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
    ) -> tuple[List[Consultation], int]:
        query = select(Consultation).where(Consultation.status == "pending")

        if category:
            query = query.where(Consultation.category == category)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Consultation.created_at.asc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        consultations = result.scalars().all()

        return list(consultations), total

    async def get_stats(self, lawyer_id: Optional[int] = None) -> dict:
        if lawyer_id:
            query = select(Consultation).where(Consultation.lawyer_id == lawyer_id)
        else:
            query = select(Consultation)

        total_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar() or 0

        pending_result = await self.db.execute(
            select(func.count()).select_from(
                query.where(Consultation.status == "pending").subquery()
            )
        )
        pending = pending_result.scalar() or 0

        processing_result = await self.db.execute(
            select(func.count()).select_from(
                query.where(Consultation.status == "processing").subquery()
            )
        )
        processing = processing_result.scalar() or 0

        answered_result = await self.db.execute(
            select(func.count()).select_from(
                query.where(Consultation.status == "answered").subquery()
            )
        )
        answered = answered_result.scalar() or 0

        return {
            "total": total,
            "pending": pending,
            "processing": processing,
            "answered": answered,
        }