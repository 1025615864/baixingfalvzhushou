"""Lawyer consultation services - 律师咨询服务"""
from datetime import datetime, timezone
from typing import Any
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_, update
from sqlalchemy.orm import selectinload

from app.models.lawfirm import LawyerConsultation, LawyerConsultationMessage


class ConsultationStatus(str, Enum):
    """咨询状态"""
    PENDING = "pending"      # 待接单
    ACCEPTED = "accepted"    # 已接单
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class LawyerConsultationService:
    """律师咨询服务"""

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        data: dict,
    ) -> LawyerConsultation:
        """创建咨询"""
        # data should be a dict from ConsultationCreate.model_dump()
        consultation = LawyerConsultation(
            **data,
            user_id=user_id,
            status=ConsultationStatus.PENDING.value
        )
        db.add(consultation)
        await db.commit()
        await db.refresh(consultation)
        return consultation

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        consultation_id: int
    ) -> LawyerConsultation | None:
        """获取咨询"""
        result = await db.execute(
            select(LawyerConsultation)
            .where(LawyerConsultation.id == consultation_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_consultations(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        *,
        load_lawyer: bool = False
    ) -> tuple[list[LawyerConsultation], int]:
        """获取用户的咨询列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            status: 状态筛选
            load_lawyer: 是否预加载律师信息（用于避免N+1）
        """
        query = select(LawyerConsultation).where(
            LawyerConsultation.user_id == user_id
        )
        count_query = select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.user_id == user_id
        )

        if status:
            query = query.where(LawyerConsultation.status == status)
            count_query = count_query.where(
                LawyerConsultation.status == status)

        # 预加载律师信息避免N+1
        if load_lawyer:
            query = query.options(selectinload(LawyerConsultation.lawyer))

        query = query.order_by(desc(LawyerConsultation.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        consultations = result.scalars().all()

        count_result = await db.execute(count_query)
        total = int(count_result.scalar() or 0)

        return list(consultations), total

    @staticmethod
    async def get_lawyer_consultations(
        db: AsyncSession,
        lawyer_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        *,
        load_user: bool = False
    ) -> tuple[list[LawyerConsultation], int]:
        """获取律师的咨询列表
        
        Args:
            db: 数据库会话
            lawyer_id: 律师ID
            page: 页码
            page_size: 每页数量
            status: 状态筛选
            load_user: 是否预加载用户信息（用于避免N+1）
        """
        query = select(LawyerConsultation).where(
            LawyerConsultation.lawyer_id == lawyer_id
        )
        count_query = select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.lawyer_id == lawyer_id
        )

        if status:
            query = query.where(LawyerConsultation.status == status)
            count_query = count_query.where(
                LawyerConsultation.status == status)

        # 预加载用户信息避免N+1
        if load_user:
            query = query.options(selectinload(LawyerConsultation.user))

        query = query.order_by(desc(LawyerConsultation.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        consultations = result.scalars().all()

        count_result = await db.execute(count_query)
        total = int(count_result.scalar() or 0)

        return list(consultations), total

    @staticmethod
    async def accept(
        db: AsyncSession,
        consultation_id: int,
        lawyer_id: int
    ) -> LawyerConsultation | None:
        """律师接单"""
        result = await db.execute(
            select(LawyerConsultation).where(
                LawyerConsultation.id == consultation_id,
                LawyerConsultation.status == ConsultationStatus.PENDING.value
            )
        )
        consultation = result.scalar_one_or_none()

        if consultation:
            consultation.status = ConsultationStatus.ACCEPTED.value
            consultation.lawyer_id = lawyer_id
            await db.commit()
            await db.refresh(consultation)

        return consultation

    @staticmethod
    async def complete(
        db: AsyncSession,
        consultation_id: int
    ) -> LawyerConsultation | None:
        """完成咨询"""
        result = await db.execute(
            select(LawyerConsultation).where(
                LawyerConsultation.id == consultation_id
            )
        )
        consultation = result.scalar_one_or_none()

        if consultation:
            consultation.status = ConsultationStatus.COMPLETED.value
            consultation.completed_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(consultation)

        return consultation

    @staticmethod
    async def get_by_user(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status_filter: str | None = None,
        *,
        load_lawyer: bool = False
    ) -> tuple[list[LawyerConsultation], int]:
        """获取用户的咨询列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            status_filter: 状态筛选
            load_lawyer: 是否预加载律师信息（用于避免N+1）
        """
        query = select(LawyerConsultation).where(
            LawyerConsultation.user_id == user_id
        )

        if status_filter:
            query = query.where(LawyerConsultation.status == status_filter)

        # 预加载律师信息避免N+1
        if load_lawyer:
            query = query.options(selectinload(LawyerConsultation.lawyer))

        query = query.order_by(desc(LawyerConsultation.created_at))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        consultations = list(result.scalars().all())

        return consultations, total

    @staticmethod
    async def update_status(
        db: AsyncSession,
        consultation_id: int,
        status: str
    ) -> LawyerConsultation | None:
        """更新咨询状态"""
        result = await db.execute(
            select(LawyerConsultation).where(
                LawyerConsultation.id == consultation_id
            )
        )
        consultation = result.scalar_one_or_none()

        if consultation:
            # 处理取消状态（退款逻辑已迁移到payment-channel-service）
            consultation.status = status
            if status == "cancelled":
                consultation.cancelled_at = datetime.now(timezone.utc)
            elif status == "completed":
                consultation.completed_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(consultation)

        return consultation


class ConsultationMessageService:
    """咨询消息服务"""

    @staticmethod
    async def create(
        db: AsyncSession,
        consultation_id: int,
        sender_id: int,
        sender_type: str,  # "user" or "lawyer"
        content: str
    ) -> LawyerConsultationMessage:
        """发送消息"""
        message = LawyerConsultationMessage(
            consultation_id=consultation_id,
            sender_user_id=sender_id,
            sender_role=sender_type,
            content=content
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        consultation_id: int,
        before: datetime | None = None,
        limit: int = 50
    ) -> list[LawyerConsultationMessage]:
        """获取消息列表"""
        query = select(LawyerConsultationMessage).where(
            LawyerConsultationMessage.consultation_id == consultation_id
        )

        if before:
            query = query.where(
                LawyerConsultationMessage.created_at < before
            )

        query = query.order_by(desc(LawyerConsultationMessage.created_at))
        query = query.limit(limit)

        result = await db.execute(query)
        messages = result.scalars().all()

        return list(reversed(messages))  # 按时间正序返回
