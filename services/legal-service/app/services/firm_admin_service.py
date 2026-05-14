"""律所管理服务 - 供律所管理员和平台管理员使用"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..models import Consultation, Lawyer, LawFirm, LawyerConsultation


class FirmAdminService:
    """律所管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_firm_consultations(
        self,
        lawfirm_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> tuple[List[Consultation], int]:
        """获取律所的咨询列表"""
        query = select(Consultation).where(
            Consultation.lawfirm_id == lawfirm_id
        )

        if status:
            query = query.where(Consultation.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Consultation.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        consultations = result.scalars().all()

        return list(consultations), total

    async def assign_consultation_to_lawyer(
        self,
        consultation_id: int,
        lawyer_id: int,
        assigned_by_user_id: int,
    ) -> Consultation:
        """将咨询分配给律所内的律师"""
        consultation_result = await self.db.execute(
            select(Consultation).where(Consultation.id == consultation_id)
        )
        consultation = consultation_result.scalar_one_or_none()

        if not consultation:
            raise ValueError("咨询不存在")

        if consultation.lawfirm_id is None:
            raise ValueError("该咨询未分配给律所")

        lawyer_result = await self.db.execute(
            select(Lawyer).where(
                and_(
                    Lawyer.id == lawyer_id,
                    Lawyer.lawfirm_id == consultation.lawfirm_id,
                )
            )
        )
        lawyer = lawyer_result.scalar_one_or_none()

        if not lawyer:
            raise ValueError("律师不属于该律所")

        consultation.lawyer_id = lawyer_id
        consultation.assigned_by_user_id = assigned_by_user_id
        consultation.assigned_at = datetime.now(timezone.utc)
        consultation.status = "processing"
        consultation.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(consultation)
        return consultation

    async def get_firm_stats(self, lawfirm_id: int) -> dict:
        """获取律所统计信息"""
        lawyers_result = await self.db.execute(
            select(func.count(Lawyer.id)).where(
                Lawyer.lawfirm_id == lawfirm_id
            )
        )
        lawyer_count = lawyers_result.scalar() or 0

        consultations_result = await self.db.execute(
            select(func.count(Consultation.id)).where(
                Consultation.lawfirm_id == lawfirm_id
            )
        )
        consultation_count = consultations_result.scalar() or 0

        active_result = await self.db.execute(
            select(func.count(Consultation.id)).where(
                and_(
                    Consultation.lawfirm_id == lawfirm_id,
                    Consultation.status.in_(["pending", "processing"]),
                )
            )
        )
        active_count = active_result.scalar() or 0

        revenue_result = await self.db.execute(
            select(func.sum(LawyerConsultation.price)).where(
                and_(
                    LawyerConsultation.lawyer_id.in_(
                        select(Lawyer.id).where(Lawyer.lawfirm_id == lawfirm_id)
                    ),
                    LawyerConsultation.status == "completed",
                )
            )
        )
        total_revenue = revenue_result.scalar() or 0.0

        return {
            "lawyer_count": lawyer_count,
            "consultation_count": consultation_count,
            "active_consultations": active_count,
            "total_revenue": float(total_revenue),
        }

    async def get_lawyer_stats(self, lawfirm_id: int) -> List[dict]:
        """获取律所内各律师的统计"""
        result = await self.db.execute(
            select(Lawyer).where(Lawyer.lawfirm_id == lawfirm_id)
        )
        lawyers = result.scalars().all()

        stats = []
        for lawyer in lawyers:
            consult_result = await self.db.execute(
                select(func.count(Consultation.id)).where(
                    Consultation.lawyer_id == lawyer.id
                )
            )
            consultation_count = consult_result.scalar() or 0

            active_result = await self.db.execute(
                select(func.count(Consultation.id)).where(
                    and_(
                        Consultation.lawyer_id == lawyer.id,
                        Consultation.status.in_(["pending", "processing"]),
                    )
                )
            )
            active_count = active_result.scalar() or 0

            stats.append({
                "lawyer_id": lawyer.id,
                "name": lawyer.name,
                "firm_role": lawyer.firm_role,
                "consultation_count": consultation_count,
                "active_consultations": active_count,
                "rating": lawyer.rating,
                "response_time": lawyer.response_time or 0,
            })

        return stats
