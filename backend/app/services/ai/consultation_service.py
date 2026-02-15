"""AI咨询会话服务"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, update

from ...models.consultation import (
    Consultation, ChatMessage, ConsultationStatus, ConsultationCategory
)
from ...models.user import User
from ...database import get_db

logger = logging.getLogger(__name__)


class ConsultationService:
    """咨询会话服务"""

    @staticmethod
    def generate_session_id() -> str:
        """生成会话ID"""
        return f"cons_{uuid.uuid4().hex[:16]}"

    @classmethod
    async def create_consultation(
        cls,
        db: AsyncSession,
        user_id: int,
        title: Optional[str] = None,
        category: str = ConsultationCategory.GENERAL,
        initial_message: Optional[str] = None
    ) -> Consultation:
        """创建新的咨询会话"""
        session_id = cls.generate_session_id()

        consultation = Consultation(
            user_id=user_id,
            session_id=session_id,
            title=title or "新咨询",
            category=category,
            status=ConsultationStatus.ACTIVE,
            message_count=0,
            total_tokens=0
        )

        db.add(consultation)
        await db.flush()
        await db.refresh(consultation)

        # 如果有初始消息，添加为第一条消息
        if initial_message:
            message = ChatMessage(
                consultation_id=consultation.id,
                role="user",
                content=initial_message
            )
            db.add(message)
            consultation.message_count = 1
            await db.flush()

        logger.info(f"Created consultation: {session_id} for user {user_id}")
        return consultation

    @classmethod
    async def get_consultation_by_session_id(
        cls,
        db: AsyncSession,
        session_id: str
    ) -> Optional[Consultation]:
        """根据会话ID获取咨询会话"""
        result = await db.execute(
            select(Consultation).where(Consultation.session_id == session_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_consultation_by_id(
        cls,
        db: AsyncSession,
        consultation_id: int
    ) -> Optional[Consultation]:
        """根据ID获取咨询会话"""
        result = await db.execute(
            select(Consultation).where(Consultation.id == consultation_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_user_consultations(
        cls,
        db: AsyncSession,
        user_id: int,
        status: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Consultation], int]:
        """获取用户的咨询会话列表"""
        query = select(Consultation).where(Consultation.user_id == user_id)

        if status:
            query = query.where(Consultation.status == status)
        if category:
            query = query.where(Consultation.category == category)

        # 获取总数
        count_query = select(func.count(Consultation.id)).where(Consultation.user_id == user_id)
        if status:
            count_query = count_query.where(Consultation.status == status)
        if category:
            count_query = count_query.where(Consultation.category == category)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(desc(Consultation.updated_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        consultations = list(result.scalars().all())

        return consultations, total

    @classmethod
    async def add_message(
        cls,
        db: AsyncSession,
        consultation_id: int,
        role: str,
        content: str,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        model: Optional[str] = None,
        latency_ms: Optional[int] = None,
        references: Optional[List[Dict]] = None,
        suggested_questions: Optional[List[str]] = None
    ) -> ChatMessage:
        """添加消息到会话"""
        # 获取咨询会话
        consultation = await cls.get_consultation_by_id(db, consultation_id)
        if not consultation:
            raise ValueError(f"Consultation not found: {consultation_id}")

        # 创建消息
        message = ChatMessage(
            consultation_id=consultation_id,
            role=role,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=model,
            latency_ms=latency_ms,
            references=json.dumps(references, ensure_ascii=False) if references else None,
            suggested_questions=json.dumps(suggested_questions, ensure_ascii=False) if suggested_questions else None
        )

        db.add(message)

        # 更新会话统计
        consultation.message_count += 1
        if total_tokens:
            consultation.total_tokens += total_tokens

        await db.flush()
        await db.refresh(message)

        return message

    @classmethod
    async def get_messages(
        cls,
        db: AsyncSession,
        consultation_id: int,
        limit: Optional[int] = None,
        before_id: Optional[int] = None
    ) -> List[ChatMessage]:
        """获取会话的消息列表"""
        query = select(ChatMessage).where(
            ChatMessage.consultation_id == consultation_id
        ).order_by(ChatMessage.created_at)

        if before_id:
            query = query.where(ChatMessage.id < before_id)

        if limit:
            query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def get_recent_messages(
        cls,
        db: AsyncSession,
        consultation_id: int,
        limit: int = 10
    ) -> List[ChatMessage]:
        """获取最近的消息"""
        query = select(ChatMessage).where(
            ChatMessage.consultation_id == consultation_id
        ).order_by(desc(ChatMessage.created_at)).limit(limit)

        result = await db.execute(query)
        messages = list(result.scalars().all())
        # 按时间正序返回
        return list(reversed(messages))

    @classmethod
    async def get_messages_for_ai_context(
        cls,
        db: AsyncSession,
        consultation_id: int,
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """获取用于AI上下文的消息历史"""
        messages = await cls.get_recent_messages(db, consultation_id, max_messages)

        context = []
        for msg in messages:
            context.append({
                "role": msg.role,
                "content": msg.content
            })

        return context

    @classmethod
    async def update_consultation_title(
        cls,
        db: AsyncSession,
        consultation_id: int,
        title: str
    ) -> Consultation:
        """更新会话标题"""
        consultation = await cls.get_consultation_by_id(db, consultation_id)
        if not consultation:
            raise ValueError(f"Consultation not found: {consultation_id}")

        consultation.title = title[:200]  # 限制长度
        await db.flush()
        await db.refresh(consultation)

        return consultation

    @classmethod
    async def update_consultation_category(
        cls,
        db: AsyncSession,
        consultation_id: int,
        category: str
    ) -> Consultation:
        """更新会话分类"""
        consultation = await cls.get_consultation_by_id(db, consultation_id)
        if not consultation:
            raise ValueError(f"Consultation not found: {consultation_id}")

        consultation.category = category
        await db.flush()
        await db.refresh(consultation)

        return consultation

    @classmethod
    async def archive_consultation(
        cls,
        db: AsyncSession,
        consultation_id: int,
        reason: Optional[str] = None
    ) -> Consultation:
        """归档会话"""
        consultation = await cls.get_consultation_by_id(db, consultation_id)
        if not consultation:
            raise ValueError(f"Consultation not found: {consultation_id}")

        consultation.status = ConsultationStatus.ARCHIVED
        consultation.archived_at = datetime.now()
        consultation.archive_reason = reason

        await db.flush()
        await db.refresh(consultation)

        logger.info(f"Archived consultation: {consultation.session_id}")
        return consultation

    @classmethod
    async def close_consultation(
        cls,
        db: AsyncSession,
        consultation_id: int
    ) -> Consultation:
        """关闭会话"""
        consultation = await cls.get_consultation_by_id(db, consultation_id)
        if not consultation:
            raise ValueError(f"Consultation not found: {consultation_id}")

        consultation.status = ConsultationStatus.CLOSED
        await db.flush()
        await db.refresh(consultation)

        return consultation

    @classmethod
    async def transfer_to_human(
        cls,
        db: AsyncSession,
        consultation_id: int,
        lawyer_id: int,
        reason: Optional[str] = None
    ) -> Consultation:
        """转人工咨询"""
        consultation = await cls.get_consultation_by_id(db, consultation_id)
        if not consultation:
            raise ValueError(f"Consultation not found: {consultation_id}")

        consultation.status = ConsultationStatus.TRANSFERRED
        consultation.is_transferred = True
        consultation.transferred_at = datetime.now()
        consultation.transferred_to = lawyer_id
        consultation.transfer_reason = reason

        await db.flush()
        await db.refresh(consultation)

        logger.info(f"Transferred consultation {consultation.session_id} to lawyer {lawyer_id}")
        return consultation

    @classmethod
    async def delete_consultation(
        cls,
        db: AsyncSession,
        consultation_id: int
    ) -> bool:
        """删除会话（软删除，实际为归档）"""
        try:
            await cls.archive_consultation(db, consultation_id, reason="用户删除")
            return True
        except Exception as e:
            logger.error(f"Failed to delete consultation {consultation_id}: {e}")
            return False

    @classmethod
    async def add_message_feedback(
        cls,
        db: AsyncSession,
        message_id: int,
        rating: int,
        feedback: Optional[str] = None,
        is_helpful: Optional[bool] = None
    ) -> ChatMessage:
        """添加消息反馈"""
        result = await db.execute(
            select(ChatMessage).where(ChatMessage.id == message_id)
        )
        message = result.scalar_one_or_none()

        if not message:
            raise ValueError(f"Message not found: {message_id}")

        message.rating = rating
        message.feedback = feedback
        message.is_helpful = is_helpful

        await db.flush()
        await db.refresh(message)

        return message

    @classmethod
    async def auto_archive_old_consultations(
        cls,
        db: AsyncSession,
        days: int = 30
    ) -> int:
        """自动归档长时间未活动的会话"""
        cutoff_date = datetime.now() - timedelta(days=days)

        result = await db.execute(
            update(Consultation)
            .where(
                Consultation.status == ConsultationStatus.ACTIVE,
                Consultation.updated_at < cutoff_date
            )
            .values(
                status=ConsultationStatus.ARCHIVED,
                archived_at=datetime.now(),
                archive_reason=f"超过{days}天未活动，自动归档"
            )
        )

        archived_count = result.rowcount
        await db.flush()

        logger.info(f"Auto-archived {archived_count} old consultations")
        return archived_count

    @classmethod
    async def get_consultation_stats(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """获取用户咨询统计"""
        # 总会话数
        total_result = await db.execute(
            select(func.count(Consultation.id)).where(Consultation.user_id == user_id)
        )
        total = total_result.scalar() or 0

        # 活跃会话数
        active_result = await db.execute(
            select(func.count(Consultation.id)).where(
                Consultation.user_id == user_id,
                Consultation.status == ConsultationStatus.ACTIVE
            )
        )
        active = active_result.scalar() or 0

        # 总消息数
        messages_result = await db.execute(
            select(func.sum(Consultation.message_count)).where(Consultation.user_id == user_id)
        )
        total_messages = messages_result.scalar() or 0

        # 总token数
        tokens_result = await db.execute(
            select(func.sum(Consultation.total_tokens)).where(Consultation.user_id == user_id)
        )
        total_tokens = tokens_result.scalar() or 0

        # 分类统计
        category_result = await db.execute(
            select(Consultation.category, func.count(Consultation.id))
            .where(Consultation.user_id == user_id)
            .group_by(Consultation.category)
        )
        categories = {cat: count for cat, count in category_result.all()}

        return {
            "total_consultations": total,
            "active_consultations": active,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "categories": categories
        }
