"""律师日程管理服务"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models.lawfirm import LawyerSchedule
from app.schemas.lawfirm import LawyerScheduleCreate, LawyerScheduleUpdate


class LawyerScheduleService:
    """律师日程服务"""

    @staticmethod
    async def create(
        db: AsyncSession,
        lawyer_id: int,
        data: LawyerScheduleCreate,
    ) -> LawyerSchedule:
        """创建日程"""
        schedule = LawyerSchedule(
            lawyer_id=lawyer_id,
            **data.model_dump()
        )
        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)
        return schedule

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        schedule_id: int,
    ) -> Optional[LawyerSchedule]:
        """根据ID获取日程"""
        result = await db.execute(
            select(LawyerSchedule).where(LawyerSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_lawyer_id(
        db: AsyncSession,
        lawyer_id: int,
        page: int = 1,
        page_size: int = 20,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[List[LawyerSchedule], int]:
        """获取律师的日程列表"""
        query = select(LawyerSchedule).where(
            LawyerSchedule.lawyer_id == lawyer_id
        )

        # 日期筛选
        if date_from:
            query = query.where(LawyerSchedule.start_time >= date_from)
        if date_to:
            query = query.where(LawyerSchedule.end_time <= date_to)

        count_query = select(func.count(LawyerSchedule.id)).where(
            LawyerSchedule.lawyer_id == lawyer_id
        )
        if date_from:
            count_query = count_query.where(
                LawyerSchedule.start_time >= date_from)
        if date_to:
            count_query = count_query.where(LawyerSchedule.end_time <= date_to)

        query = query.order_by(LawyerSchedule.start_time)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        schedules = result.scalars().all()

        count_result = await db.execute(count_query)
        total = int(count_result.scalar() or 0)

        return list(schedules), total

    @staticmethod
    async def update(
        db: AsyncSession,
        schedule_id: int,
        data: LawyerScheduleUpdate,
    ) -> Optional[LawyerSchedule]:
        """更新日程"""
        schedule = await LawyerScheduleService.get_by_id(db, schedule_id)
        if not schedule:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)

        await db.commit()
        await db.refresh(schedule)
        return schedule

    @staticmethod
    async def delete(
        db: AsyncSession,
        schedule_id: int,
    ) -> bool:
        """删除日程"""
        schedule = await LawyerScheduleService.get_by_id(db, schedule_id)
        if not schedule:
            return False

        await db.delete(schedule)
        await db.commit()
        return True

    @staticmethod
    async def get_available_slots(
        db: AsyncSession,
        lawyer_id: int,
        date: datetime,
        duration_minutes: int = 30,
    ) -> List[dict]:
        """获取律师可用时间段"""
        # 获取该律师当天的所有日程
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        schedules = await db.execute(
            select(LawyerSchedule).where(
                LawyerSchedule.lawyer_id == lawyer_id,
                LawyerSchedule.date >= start_of_day,
                LawyerSchedule.date < end_of_day,
            ).order_by(LawyerSchedule.start_time)
        )
        schedules = schedules.scalars().all()

        # 默认工作时间段 (9:00-17:00)
        work_start = start_of_day.replace(hour=9, minute=0)
        work_end = start_of_day.replace(hour=17, minute=0)

        # 生成时间段
        slots = []
        current_time = work_start

        while current_time + timedelta(minutes=duration_minutes) <= work_end:
            slot_end = current_time + timedelta(minutes=duration_minutes)

            # 检查时间段是否与现有日程冲突
            conflict = False
            for schedule in schedules:
                # 将字符串时间转换为 datetime 对象进行比较
                schedule_start = datetime.strptime(
                    f"{schedule.date.strftime('%Y-%m-%d')} {schedule.start_time}", "%Y-%m-%d %H:%M")
                schedule_end = datetime.strptime(
                    f"{schedule.date.strftime('%Y-%m-%d')} {schedule.end_time}", "%Y-%m-%d %H:%M")
                if (current_time < schedule_end and
                        slot_end > schedule_start):
                    conflict = True
                    break

            if not conflict:
                slots.append({
                    'start_time': current_time,
                    'end_time': slot_end,
                    'available': True
                })

            current_time += timedelta(minutes=30)  # 默认30分钟间隔

        return slots

    @staticmethod
    async def has_conflict(
        db: AsyncSession,
        lawyer_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_schedule_id: Optional[int] = None,
    ) -> bool:
        """检查时间段是否冲突"""
        query = select(LawyerSchedule).where(
            LawyerSchedule.lawyer_id == lawyer_id,
            LawyerSchedule.start_time < end_time,
            LawyerSchedule.end_time > start_time,
        )

        if exclude_schedule_id:
            query = query.where(LawyerSchedule.id != exclude_schedule_id)

        result = await db.execute(query)
        conflicting_schedule = result.scalar_one_or_none()

        return conflicting_schedule is not None
