"""排班服务"""
from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..models import LawyerSchedule


class ScheduleService:
    """排班服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        lawyer_id: int,
        schedule_date: date,
        start_time: str,
        end_time: str,
    ) -> LawyerSchedule:
        """创建排班"""
        schedule = LawyerSchedule(
            lawyer_id=lawyer_id,
            date=datetime.combine(schedule_date, datetime.min.time()),
            start_time=start_time,
            end_time=end_time,
            is_available=True,
        )
        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    async def bulk_create(
        self,
        lawyer_id: int,
        schedules: List[dict],
    ) -> List[LawyerSchedule]:
        """批量创建排班"""
        created = []
        for item in schedules:
            schedule = LawyerSchedule(
                lawyer_id=lawyer_id,
                date=datetime.combine(item["date"], datetime.min.time()),
                start_time=item["start_time"],
                end_time=item["end_time"],
                is_available=True,
            )
            self.db.add(schedule)
            created.append(schedule)
        await self.db.commit()
        for s in created:
            await self.db.refresh(s)
        return created

    async def get(
        self,
        schedule_id: int,
    ) -> Optional[LawyerSchedule]:
        """获取排班"""
        result = await self.db.execute(
            select(LawyerSchedule).where(LawyerSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def get_by_lawyer_date(
        self,
        lawyer_id: int,
        schedule_date: date,
    ) -> List[LawyerSchedule]:
        """获取律师某天的排班"""
        result = await self.db.execute(
            select(LawyerSchedule).where(
                and_(
                    LawyerSchedule.lawyer_id == lawyer_id,
                    func.date(LawyerSchedule.date) == schedule_date,
                )
            ).order_by(LawyerSchedule.start_time)
        )
        return list(result.scalars().all())

    async def get_by_lawyer_month(
        self,
        lawyer_id: int,
        year: int,
        month: int,
    ) -> List[LawyerSchedule]:
        """获取律师某月的排班"""
        from calendar import monthrange
        _, last_day = monthrange(year, month)
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, last_day, 23, 59, 59)

        result = await self.db.execute(
            select(LawyerSchedule).where(
                and_(
                    LawyerSchedule.lawyer_id == lawyer_id,
                    LawyerSchedule.date >= start_date,
                    LawyerSchedule.date <= end_date,
                )
            ).order_by(LawyerSchedule.date, LawyerSchedule.start_time)
        )
        return list(result.scalars().all())

    async def update_availability(
        self,
        schedule_id: int,
        is_available: bool,
    ) -> Optional[LawyerSchedule]:
        """更新可用性"""
        schedule = await self.get(schedule_id)
        if not schedule:
            return None
        schedule.is_available = is_available
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    async def delete(self, schedule_id: int) -> bool:
        """删除排班"""
        schedule = await self.get(schedule_id)
        if not schedule:
            return False
        await self.db.delete(schedule)
        await self.db.commit()
        return True

    async def delete_by_lawyer_date(
        self,
        lawyer_id: int,
        schedule_date: date,
    ) -> int:
        """删除律师某天的所有排班"""
        result = await self.db.execute(
            select(LawyerSchedule).where(
                and_(
                    LawyerSchedule.lawyer_id == lawyer_id,
                    func.date(LawyerSchedule.date) == schedule_date,
                )
            )
        )
        schedules = result.scalars().all()
        count = len(schedules)
        for s in schedules:
            await self.db.delete(s)
        await self.db.commit()
        return count