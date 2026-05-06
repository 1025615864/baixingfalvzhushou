"""预约服务"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..database import TransactionManager
from ..models import LawyerConsultation, Lawyer, LawyerSchedule
from ..cache.redis_lock import lock_manager
from ..shared.appointment_state_machine import AppointmentStatus, AppointmentStateMachine


class AppointmentService:
    """预约服务"""

    PAYMENT_TIMEOUT_MINUTES = 30

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        consultation_id: int,
        lawyer_id: int,
        appointment_type: str,
        scheduled_at: datetime,
        price: float = 0.0,
    ) -> LawyerConsultation:
        """创建预约（并发安全）"""
        schedule_id = None
        lock_value = None

        try:
            lock_key = f"appointment:create:{lawyer_id}:{scheduled_at.isoformat()}"
            lock_value = await lock_manager.acquire_lock(lock_key, timeout=10, lock_timeout=30)
            if not lock_value:
                raise Exception("无法获取锁，请稍后重试")

            async with self.db.begin():
                schedule_result = await self.db.execute(
                    select(LawyerSchedule)
                    .where(
                        and_(
                            LawyerSchedule.lawyer_id == lawyer_id,
                            func.date(LawyerSchedule.date) == scheduled_at.date(),
                            LawyerSchedule.is_available == True,
                        )
                    )
                    .with_for_update()
                )
                schedule = schedule_result.scalar_one_or_none()

                if not schedule:
                    raise Exception("该时段不可预约")

                existing_result = await self.db.execute(
                    select(LawyerConsultation).where(
                        and_(
                            LawyerConsultation.lawyer_id == lawyer_id,
                            LawyerConsultation.scheduled_at == scheduled_at,
                            LawyerConsultation.status.in_(["pending", "confirmed"]),
                        )
                    ).with_for_update()
                )
                existing = existing_result.scalar_one_or_none()
                if existing:
                    raise Exception("该时段已被预约")

                appointment = LawyerConsultation(
                    consultation_id=consultation_id,
                    lawyer_id=lawyer_id,
                    type=appointment_type,
                    scheduled_at=scheduled_at,
                    price=price,
                    status=AppointmentStatus.PENDING_PAYMENT.value,
                )
                self.db.add(appointment)
                await self.db.flush()
                await self.db.refresh(appointment)
                return appointment

        finally:
            if lock_value:
                await lock_manager.release_lock(
                    f"appointment:create:{lawyer_id}:{scheduled_at.isoformat()}",
                    lock_value
                )

    async def get(self, appointment_id: int) -> Optional[LawyerConsultation]:
        """获取预约"""
        result = await self.db.execute(
            select(LawyerConsultation).where(LawyerConsultation.id == appointment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_consultation(self, consultation_id: int) -> Optional[LawyerConsultation]:
        """通过咨询ID获取预约"""
        result = await self.db.execute(
            select(LawyerConsultation).where(
                LawyerConsultation.consultation_id == consultation_id
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[LawyerConsultation], int]:
        """获取用户的预约列表"""
        query = select(LawyerConsultation).where(
            LawyerConsultation.consultation_id.in_(
                select(LawyerConsultation.consultation_id)
            )
        )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(LawyerConsultation.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        appointments = result.scalars().all()

        return list(appointments), total

    async def list_by_lawyer(
        self,
        lawyer_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[LawyerConsultation], int]:
        """获取律师的预约列表"""
        query = select(LawyerConsultation).where(
            LawyerConsultation.lawyer_id == lawyer_id
        )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(LawyerConsultation.scheduled_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        appointments = result.scalars().all()

        return list(appointments), total

    async def update_status(
        self,
        appointment_id: int,
        new_status: str,
    ) -> Optional[LawyerConsultation]:
        """更新预约状态"""
        appointment = await self.get(appointment_id)
        if not appointment:
            return None

        if not AppointmentStateMachine.can_transition_from(appointment.status, new_status):
            from ..shared.state_machines import TransitionError
            raise TransitionError(
                current_state=appointment.status,
                target_state=new_status,
                message=f"不允许的状态转换: {appointment.status} -> {new_status}"
            )

        appointment.status = new_status
        appointment.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def cancel(self, appointment_id: int) -> Optional[LawyerConsultation]:
        """取消预约"""
        return await self.update_status(appointment_id, AppointmentStatus.CANCELLED_BY_USER.value)

    async def accept(self, appointment_id: int) -> Optional[LawyerConsultation]:
        """接受预约（确认）"""
        return await self.update_status(appointment_id, AppointmentStatus.CONFIRMED.value)

    async def get_available_slots(
        self,
        lawyer_id: int,
        date: datetime,
    ) -> List[dict]:
        """获取律师某天的可用时段"""
        schedules_result = await self.db.execute(
            select(LawyerSchedule).where(
                and_(
                    LawyerSchedule.lawyer_id == lawyer_id,
                    func.date(LawyerSchedule.date) == date.date(),
                    LawyerSchedule.is_available == True,
                )
            )
        )
        schedules = schedules_result.scalars().all()

        booked_result = await self.db.execute(
            select(LawyerConsultation).where(
                and_(
                    LawyerConsultation.lawyer_id == lawyer_id,
                    func.date(LawyerConsultation.scheduled_at) == date.date(),
                    LawyerConsultation.status.in_([
                        AppointmentStatus.PENDING_PAYMENT.value,
                        AppointmentStatus.CONFIRMED.value,
                    ]),
                )
            )
        )
        booked = booked_result.scalars().all()
        booked_times = {(b.scheduled_at.hour, b.scheduled_at.minute) for b in booked if b.scheduled_at}

        slots = []
        for schedule in schedules:
            slots.append({
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "is_available": True,
            })

        return slots

    async def check_time_conflict(
        self,
        lawyer_id: int,
        scheduled_at: datetime,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """检查时间冲突"""
        query = select(LawyerConsultation).where(
            and_(
                LawyerConsultation.lawyer_id == lawyer_id,
                LawyerConsultation.scheduled_at == scheduled_at,
                LawyerConsultation.status.in_([
                    AppointmentStatus.PENDING_PAYMENT.value,
                    AppointmentStatus.CONFIRMED.value,
                ]),
            )
        )
        if exclude_id:
            query = query.where(LawyerConsultation.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def handle_timeout_appointments(self) -> dict:
        """处理超时未支付的预约（后台任务）"""
        timeout_threshold = datetime.utcnow() - timedelta(minutes=self.PAYMENT_TIMEOUT_MINUTES)

        result = await self.db.execute(
            select(LawyerConsultation).where(
                and_(
                    LawyerConsultation.status == AppointmentStatus.PENDING_PAYMENT.value,
                    LawyerConsultation.scheduled_at < timeout_threshold,
                )
            ).with_for_update(skip_locked=True)
        )
        timed_out_appointments = result.scalars().all()

        released_slots = 0
        expired_count = 0

        for appointment in timed_out_appointments:
            appointment.status = AppointmentStatus.EXPIRED.value
            appointment.updated_at = datetime.utcnow()
            expired_count += 1

            released_slots += 1

        if expired_count > 0:
            await self.db.commit()

        return {
            "expired_count": expired_count,
            "released_slots": released_slots,
        }

    async def handle_scheduled_time_past(self) -> dict:
        """处理已过预约时间但未完成的预约（后台任务）"""
        now = datetime.utcnow()
        completion_threshold = now - timedelta(minutes=30)

        result = await self.db.execute(
            select(LawyerConsultation).where(
                and_(
                    LawyerConsultation.status == AppointmentStatus.CONFIRMED.value,
                    LawyerConsultation.scheduled_at < completion_threshold,
                )
            ).with_for_update(skip_locked=True)
        )
        past_appointments = result.scalars().all()

        no_show_count = 0
        for appointment in past_appointments:
            appointment.status = AppointmentStatus.NO_SHOW.value
            appointment.updated_at = datetime.utcnow()
            no_show_count += 1

        if no_show_count > 0:
            await self.db.commit()

        return {
            "no_show_count": no_show_count,
        }