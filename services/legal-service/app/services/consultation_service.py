"""咨询务"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import Consultation, ChatMessage


class ConsultationService:
    """咨询服务"""

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
        """创建咨询"""
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
        return consultation

    async def get(self, consultation_id: int) -> Optional[Consultation]:
        """获取咨询"""
        result = await self.db.execute(
            select(Consultation).where(Consultation.id == consultation_id)
        )
        return result.scalar_one_or_none()

    async def get_messages(self, consultation_id: int) -> List[ChatMessage]:
        """获取咨询消息"""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.consultation_id == consultation_id)
            .order_by(ChatMessage.created_at)
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        consultation_id: int,
        role: str,
        content: str,
    ) -> ChatMessage:
        """添加消息"""
        message = ChatMessage(
            consultation_id=consultation_id,
            role=role,
            content=content,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message
