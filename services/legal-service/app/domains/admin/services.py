"""管理领域服务"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ...models import Lawyer, Consultation, LawFirm, LawFirmVerification, Review
from ...cache.lawyer_cache import LawyerCache, FirmCache


class AdminDomainService:
    """管理领域服务 - 平台级管理操作"""

    def __init__(self, db: AsyncSession, lawyer_cache: LawyerCache = None, firm_cache: FirmCache = None):
        self.db = db
        self.lawyer_cache = lawyer_cache
        self.firm_cache = firm_cache

    async def get_platform_stats(self) -> dict:
        total_lawyers_result = await self.db.execute(
            select(func.count()).select_from(Lawyer)
        )
        total_lawyers = total_lawyers_result.scalar() or 0

        verified_lawyers_result = await self.db.execute(
            select(func.count()).select_from(Lawyer).where(Lawyer.status == "verified")
        )
        verified_lawyers = verified_lawyers_result.scalar() or 0

        total_consultations_result = await self.db.execute(
            select(func.count()).select_from(Consultation)
        )
        total_consultations = total_consultations_result.scalar() or 0

        pending_consultations_result = await self.db.execute(
            select(func.count()).select_from(Consultation).where(Consultation.status == "pending")
        )
        pending_consultations = pending_consultations_result.scalar() or 0

        total_firms_result = await self.db.execute(
            select(func.count()).select_from(LawFirm)
        )
        total_firms = total_firms_result.scalar() or 0

        pending_verifications_result = await self.db.execute(
            select(func.count()).select_from(LawFirmVerification).where(
                LawFirmVerification.status == "pending"
            )
        )
        pending_verifications = pending_verifications_result.scalar() or 0

        return {
            "total_lawyers": total_lawyers,
            "verified_lawyers": verified_lawyers,
            "total_consultations": total_consultations,
            "pending_consultations": pending_consultations,
            "total_firms": total_firms,
            "pending_verifications": pending_verifications,
        }

    async def list_pending_verifications(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[LawFirmVerification], int]:
        query = select(LawFirmVerification).where(
            LawFirmVerification.status == "pending"
        )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(LawFirmVerification.created_at.asc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        verifications = result.scalars().all()

        return list(verifications), total

    async def review_verification(
        self,
        verification_id: int,
        decision: str,
        reason: Optional[str] = None,
    ) -> Optional[LawFirmVerification]:
        result = await self.db.execute(
            select(LawFirmVerification).where(LawFirmVerification.id == verification_id)
        )
        verification = result.scalar_one_or_none()
        if not verification:
            return None

        verification.status = decision
        verification.reviewed_at = datetime.utcnow()
        verification.review_reason = reason
        await self.db.commit()
        await self.db.refresh(verification)

        if decision == "approved" and verification.firm_id:
            firm_result = await self.db.execute(
                select(LawFirm).where(LawFirm.id == verification.firm_id)
            )
            firm = firm_result.scalar_one_or_none()
            if firm:
                firm.status = "active"
                firm.verified_at = datetime.utcnow()
                await self.db.commit()

                if self.firm_cache:
                    await self.firm_cache.invalidate_firm_detail(firm.id)
                    await self.firm_cache.invalidate_firm_list()

        return verification

    async def list_all_lawyers(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> tuple[List[Lawyer], int]:
        query = select(Lawyer)

        if status:
            query = query.where(Lawyer.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Lawyer.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        lawyers = result.scalars().all()

        return list(lawyers), total

    async def suspend_lawyer(self, lawyer_id: int, reason: str) -> Optional[Lawyer]:
        result = await self.db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        lawyer = result.scalar_one_or_none()
        if not lawyer:
            return None

        lawyer.status = "suspended"
        lawyer.suspended_at = datetime.utcnow()
        lawyer.suspension_reason = reason
        await self.db.commit()
        await self.db.refresh(lawyer)

        if self.lawyer_cache:
            await self.lawyer_cache.invalidate_lawyer_detail(lawyer_id)
            await self.lawyer_cache.invalidate_lawyer_list()

        return lawyer

    async def reactivate_lawyer(self, lawyer_id: int) -> Optional[Lawyer]:
        result = await self.db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        lawyer = result.scalar_one_or_none()
        if not lawyer:
            return None

        lawyer.status = "verified"
        lawyer.suspended_at = None
        lawyer.suspension_reason = None
        await self.db.commit()
        await self.db.refresh(lawyer)

        if self.lawyer_cache:
            await self.lawyer_cache.invalidate_lawyer_detail(lawyer_id)
            await self.lawyer_cache.invalidate_lawyer_list()

        return lawyer

    async def get_consultation_stats(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> dict:
        query = select(Consultation)

        if start_date:
            query = query.where(Consultation.created_at >= start_date)
        if end_date:
            query = query.where(Consultation.created_at <= end_date)

        total_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar() or 0

        by_status = {}
        for status in ["pending", "processing", "answered", "cancelled"]:
            count_result = await self.db.execute(
                select(func.count()).select_from(
                    query.where(Consultation.status == status).subquery()
                )
            )
            by_status[status] = count_result.scalar() or 0

        return {
            "total": total,
            "by_status": by_status,
        }

    async def get_lawyer_ratings_report(self) -> List[dict]:
        result = await self.db.execute(
            select(
                Lawyer.id,
                Lawyer.name,
                Lawyer.rating,
                Lawyer.rating_count,
                func.count(Review.id).label("review_count"),
            )
            .join(Review, Review.lawyer_id == Lawyer.id, isouter=True)
            .group_by(Lawyer.id)
            .order_by(Lawyer.rating.desc())
            .limit(100)
        )
        rows = result.all()

        return [
            {
                "lawyer_id": row.id,
                "name": row.name,
                "rating": row.rating,
                "rating_count": row.rating_count,
                "review_count": row.review_count,
            }
            for row in rows
        ]