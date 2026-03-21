"""视频咨询服务

提供视频咨询预约、排班、会员权益计算等功能。
"""
import logging
import secrets
import string
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.video_consultation import VideoConsultation, VideoConsultationUsage, VideoSchedule
from ..models.lawfirm import Lawyer
from ..models.payment import PaymentOrder, PaymentStatus
from ..models.user import User
from ..models.membership import Membership
from .membership_service import membership_service, MembershipTier

logger = logging.getLogger(__name__)


class VideoConsultationStatus(str, Enum):
    """视频咨询状态"""
    PENDING = "pending"      # 待确认
    CONFIRMED = "confirmed"   # 已确认
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class VideoConsultationService:
    """视频咨询服务"""

    def __init__(self):
        # 默认视频咨询费用配置
        self._default_fee = 99.0  # 默认99元/30分钟
        self._default_duration = 30  # 默认30分钟

    def _generate_meeting_id(self) -> str:
        """生成会议房间ID"""
        return f"VC{secrets.token_hex(6).upper()}"

    def _generate_meeting_password(self) -> str:
        """生成会议密码"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))

    async def get_video_consultation_fee(
        self, db: AsyncSession, lawyer_id: int
    ) -> dict[str, Any]:
        """获取律师视频咨询费用设置
        
        Args:
            db: 数据库会话
            lawyer_id: 律师ID
            
        Returns:
            费用信息
        """
        result = await db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        lawyer = result.scalar_one_or_none()
        
        if not lawyer:
            return {
                "fee": self._default_fee,
                "duration": self._default_duration,
                "enabled": False
            }
        
        # 优先使用律师设置的咨询费用，如果没有则使用默认值
        fee = lawyer.consultation_fee if lawyer.consultation_fee > 0 else self._default_fee
        
        return {
            "fee": fee,
            "duration": self._default_duration,
            "enabled": True
        }

    async def calculate_member_discount(
        self, db: AsyncSession, user: User
    ) -> dict[str, Any]:
        """计算用户会员折扣
        
        Args:
            db: 数据库会话
            user: 用户
            
        Returns:
            折扣信息
        """
        tier = await membership_service.get_user_tier(db, user)
        benefits = membership_service.get_benefits(tier)
        
        if not benefits:
            return {
                "tier": MembershipTier.FREE.value,
                "discount_rate": 1.0,
                "free_monthly_count": 0,
                "is_free": False
            }
        
        discount_rate = benefits.get("video_consultation_discount", 1.0)
        free_monthly_count = benefits.get("free_video_consultations_per_month", 0)
        is_free = discount_rate == 0.0
        
        return {
            "tier": tier,
            "discount_rate": discount_rate,
            "free_monthly_count": free_monthly_count,
            "is_free": is_free
        }

    async def get_user_usage(
        self, db: AsyncSession, user_id: int
    ) -> dict[str, Any]:
        """获取用户本月视频咨询使用情况
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            使用情况
        """
        now = datetime.now(timezone.utc)
        year_month = now.strftime("%Y-%m")
        
        result = await db.execute(
            select(VideoConsultationUsage).where(
                VideoConsultationUsage.user_id == user_id,
                VideoConsultationUsage.year_month == year_month
            )
        )
        usage = result.scalar_one_or_none()
        
        if not usage:
            return {
                "year_month": year_month,
                "free_used": 0,
                "paid_count": 0,
                "remaining_free": 0
            }
        
        # 获取会员权益确定免费次数
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        discount_info = await self.calculate_member_discount(db, user)
        free_total = discount_info.get("free_monthly_count", 0)
        
        # 999表示无限
        if free_total >= 999:
            remaining_free = 999  # 无限
        else:
            remaining_free = free_total - usage.free_used
        
        return {
            "year_month": year_month,
            "free_used": usage.free_used,
            "paid_count": usage.paid_count,
            "remaining_free": remaining_free,
            "tier": discount_info.get("tier")
        }

    async def create_booking(
        self,
        db: AsyncSession,
        user: User,
        lawyer_id: int,
        scheduled_time: datetime,
        subject: str,
        description: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        """创建视频咨询预约
        
        Args:
            db: 数据库会话
            user: 用户
            lawyer_id: 律师ID
            scheduled_time: 预约时间
            subject: 咨询主题
            description: 问题描述
            category: 案件类型
            
        Returns:
            预约结果
        """
        # 获取律师信息
        lawyer_result = await db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        lawyer = lawyer_result.scalar_one_or_none()
        
        if not lawyer:
            raise ValueError("律师不存在")
        
        # 获取费用和折扣
        fee_info = await self.get_video_consultation_fee(db, lawyer_id)
        discount_info = await self.calculate_member_discount(db, user)
        
        # 计算实际费用
        base_fee = fee_info.get("fee", self._default_fee)
        discount_rate = discount_info.get("discount_rate", 1.0)
        
        # 判断是否使用免费次数
        usage = await self.get_user_usage(db, user.id)
        remaining_free = usage.get("remaining_free", 0)
        
        is_free = False
        actual_fee = base_fee * discount_rate
        
        if remaining_free > 0 and discount_info.get("is_free"):
            is_free = True
            actual_fee = 0.0
            # 扣除免费次数
            await self._use_free_次数(db, user.id)
        
        # 创建预约
        consultation = VideoConsultation(
            user_id=user.id,
            lawyer_id=lawyer_id,
            subject=subject,
            description=description,
            category=category,
            scheduled_time=scheduled_time,
            duration_minutes=fee_info.get("duration", self._default_duration),
            meeting_room_id=self._generate_meeting_id(),
            meeting_password=self._generate_meeting_password() if not is_free else None,
            status=VideoConsultationStatus.PENDING.value,
            payment_status="pending" if actual_fee > 0 else "paid",
            payment_amount=actual_fee,
            is_free=is_free,
            discount_rate=discount_rate,
        )
        db.add(consultation)
        await db.commit()
        await db.refresh(consultation)
        
        return {
            "id": consultation.id,
            "lawyer_id": lawyer_id,
            "lawyer_name": lawyer.name,
            "subject": subject,
            "scheduled_time": scheduled_time,
            "duration_minutes": consultation.duration_minutes,
            "meeting_room_id": consultation.meeting_room_id,
            "meeting_password": consultation.meeting_password,
            "base_fee": base_fee,
            "discount_rate": discount_rate,
            "actual_fee": actual_fee,
            "is_free": is_free,
            "payment_status": consultation.payment_status,
            "status": consultation.status,
            "tier": discount_info.get("tier"),
        }

    async def _use_free_次数(self, db: AsyncSession, user_id: int) -> None:
        """使用一次免费视频咨询次数"""
        now = datetime.now(timezone.utc)
        year_month = now.strftime("%Y-%m")
        
        result = await db.execute(
            select(VideoConsultationUsage).where(
                VideoConsultationUsage.user_id == user_id,
                VideoConsultationUsage.year_month == year_month
            )
        )
        usage = result.scalar_one_or_none()
        
        if usage:
            usage.free_used += 1
        else:
            usage = VideoConsultationUsage(
                user_id=user_id,
                year_month=year_month,
                free_used=1,
            )
            db.add(usage)
        
        await db.commit()

    async def get_by_id(
        self, db: AsyncSession, consultation_id: int
    ) -> VideoConsultation | None:
        """获取视频咨询详情"""
        result = await db.execute(
            select(VideoConsultation).where(
                VideoConsultation.id == consultation_id
            )
        )
        return result.scalar_one_or_none()

    async def get_user_bookings(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[VideoConsultation], int]:
        """获取用户视频咨询列表"""
        query = select(VideoConsultation).where(
            VideoConsultation.user_id == user_id
        )
        
        if status:
            query = query.where(VideoConsultation.status == status)
        
        count_query = select(func.count(VideoConsultation.id)).where(
            VideoConsultation.user_id == user_id
        )
        if status:
            count_query = count_query.where(
                VideoConsultation.status == status)
        
        query = query.order_by(VideoConsultation.scheduled_time.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        consultations = result.scalars().all()
        
        count_result = await db.execute(count_query)
        total = int(count_result.scalar() or 0)
        
        return list(consultations), total

    async def confirm_booking(
        self, db: AsyncSession, consultation_id: int
    ) -> VideoConsultation | None:
        """确认视频咨询预约"""
        consultation = await self.get_by_id(db, consultation_id)
        if not consultation:
            return None
        
        if consultation.status != VideoConsultationStatus.PENDING.value:
            raise ValueError("只能确认待确认状态的预约")
        
        consultation.status = VideoConsultationStatus.CONFIRMED.value
        await db.commit()
        await db.refresh(consultation)
        
        return consultation

    async def start_consultation(
        self, db: AsyncSession, consultation_id: int
    ) -> VideoConsultation | None:
        """开始视频咨询"""
        consultation = await self.get_by_id(db, consultation_id)
        if not consultation:
            return None
        
        if consultation.status not in [
            VideoConsultationStatus.PENDING.value,
            VideoConsultationStatus.CONFIRMED.value
        ]:
            raise ValueError("只能在确认后开始咨询")
        
        consultation.status = VideoConsultationStatus.IN_PROGRESS.value
        consultation.started_at = datetime.now(timezone.utc)
        
        # 生成会议链接（这里可以集成第三方视频SDK）
        if consultation.meeting_url is None:
            consultation.meeting_url = f"https://meeting.example.com/{consultation.meeting_room_id}"
        
        await db.commit()
        await db.refresh(consultation)
        
        return consultation

    async def end_consultation(
        self, db: AsyncSession, consultation_id: int
    ) -> VideoConsultation | None:
        """结束视频咨询"""
        consultation = await self.get_by_id(db, consultation_id)
        if not consultation:
            return None
        
        if consultation.status != VideoConsultationStatus.IN_PROGRESS.value:
            raise ValueError("只能结束进行中的咨询")
        
        consultation.status = VideoConsultationStatus.COMPLETED.value
        consultation.ended_at = datetime.now(timezone.utc)
        consultation.completed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(consultation)
        
        return consultation

    async def cancel_booking(
        self, db: AsyncSession, consultation_id: int, user_id: int
    ) -> VideoConsultation | None:
        """取消视频咨询预约"""
        consultation = await self.get_by_id(db, consultation_id)
        if not consultation:
            return None
        
        if consultation.user_id != user_id:
            raise ValueError("无权操作")
        
        if consultation.status in [
            VideoConsultationStatus.COMPLETED.value,
            VideoConsultationStatus.CANCELLED.value
        ]:
            raise ValueError("无法取消该预约")
        
        consultation.status = VideoConsultationStatus.CANCELLED.value
        consultation.cancelled_at = datetime.now(timezone.utc)
        
        # 如果是免费的，退还免费次数
        if consultation.is_free:
            await self._refund_free_次数(db, user_id)
        
        await db.commit()
        await db.refresh(consultation)
        
        return consultation

    async def _refund_free_次数(self, db: AsyncSession, user_id: int) -> None:
        """退还免费视频咨询次数"""
        now = datetime.now(timezone.utc)
        year_month = now.strftime("%Y-%m")
        
        result = await db.execute(
            select(VideoConsultationUsage).where(
                VideoConsultationUsage.user_id == user_id,
                VideoConsultationUsage.year_month == year_month
            )
        )
        usage = result.scalar_one_or_none()
        
        if usage and usage.free_used > 0:
            usage.free_used -= 1
            await db.commit()


class VideoScheduleService:
    """律师视频排班服务"""

    async def create_schedule(
        self,
        db: AsyncSession,
        lawyer_id: int,
        date: datetime,
        start_time: str,
        end_time: str,
        video_consultation_enabled: bool = True,
        consultation_fee: float = 0.0,
        max_bookings: int = 3,
        note: str | None = None,
    ) -> VideoSchedule:
        """创建视频咨询排班"""
        schedule = VideoSchedule(
            lawyer_id=lawyer_id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            video_consultation_enabled=video_consultation_enabled,
            consultation_fee=consultation_fee,
            max_bookings=max_bookings,
            note=note,
        )
        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)
        
        return schedule

    async def get_available_slots(
        self,
        db: AsyncSession,
        lawyer_id: int,
        date: datetime,
    ) -> list[dict[str, Any]]:
        """获取律师可用视频咨询时段"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        result = await db.execute(
            select(VideoSchedule).where(
                VideoSchedule.lawyer_id == lawyer_id,
                VideoSchedule.date >= start_of_day,
                VideoSchedule.date < end_of_day,
                VideoSchedule.is_available == True,
                VideoSchedule.video_consultation_enabled == True,
            ).order_by(VideoSchedule.start_time)
        )
        schedules = result.scalars().all()
        
        slots = []
        for s in schedules:
            if s.current_bookings < s.max_bookings:
                slots.append({
                    "schedule_id": s.id,
                    "date": s.date,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "consultation_fee": s.consultation_fee,
                    "available_count": s.max_bookings - s.current_bookings,
                })
        
        return slots

    async def book_slot(
        self,
        db: AsyncSession,
        schedule_id: int,
        consultation_id: int,
    ) -> VideoSchedule | None:
        """预约时段"""
        result = await db.execute(
            select(VideoSchedule).where(VideoSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            return None
        
        if schedule.current_bookings >= schedule.max_bookings:
            raise ValueError("该时段已满")
        
        schedule.current_bookings += 1
        await db.commit()
        await db.refresh(schedule)
        
        return schedule

    async def release_slot(
        self,
        db: AsyncSession,
        schedule_id: int,
    ) -> VideoSchedule | None:
        """释放时段"""
        result = await db.execute(
            select(VideoSchedule).where(VideoSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            return None
        
        if schedule.current_bookings > 0:
            schedule.current_bookings -= 1
            await db.commit()
            await db.refresh(schedule)
        
        return schedule


# 导出服务实例
video_consultation_service = VideoConsultationService()
video_schedule_service = VideoScheduleService()