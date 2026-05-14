"""数据分析服务"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case as sql_case
from ..models import Consultation, Lawyer, LawCase


class AnalyticsService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, lawyer_id: int) -> dict:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = today.replace(day=1)

        today_cons = await self.db.scalar(
            select(func.count(Consultation.id)).where(
                and_(Consultation.lawyer_id == lawyer_id, Consultation.created_at >= today)
            )
        )

        month_cases = await self.db.scalar(
            select(func.count(LawCase.id)).where(
                and_(LawCase.lawyer_id == lawyer_id, LawCase.created_at >= month_start)
            )
        )

        lawyer = await self.db.get(Lawyer, lawyer_id)

        return {
            "today_consultations": today_cons or 0,
            "month_cases": month_cases or 0,
            "rating": round(lawyer.rating, 1) if lawyer and lawyer.rating else 0.0,
            "review_count": lawyer.rating_count if lawyer else 0,
            "response_time_minutes": lawyer.response_time if lawyer else 0,
            "estimated_monthly_income": 0.0,
        }

    async def get_trends(self, lawyer_id: int, days: int = 30) -> list:
        start_date = datetime.now() - timedelta(days=days)
        trends = []

        for i in range(days):
            day = (start_date + timedelta(days=i)).date()
            day_start = datetime.combine(day, datetime.min.time())
            day_end = datetime.combine(day, datetime.max.time())

            cons_count = await self.db.scalar(
                select(func.count(Consultation.id)).where(
                    and_(
                        Consultation.lawyer_id == lawyer_id,
                        Consultation.created_at >= day_start,
                        Consultation.created_at <= day_end,
                    )
                )
            )

            case_count = await self.db.scalar(
                select(func.count(LawCase.id)).where(
                    and_(
                        LawCase.lawyer_id == lawyer_id,
                        LawCase.created_at >= day_start,
                        LawCase.created_at <= day_end,
                    )
                )
            )

            trends.append({
                "date": day.isoformat(),
                "consultations": cons_count or 0,
                "cases": case_count or 0,
            })

        return trends

    async def get_channel_distribution(self, lawyer_id: int) -> list:
        result = await self.db.execute(
            select(LawCase.source, func.count(LawCase.id))
            .where(LawCase.lawyer_id == lawyer_id)
            .group_by(LawCase.source)
        )
        rows = result.all()
        return [{"channel": row[0] or "other", "count": row[1]} for row in rows]

    async def get_ranking(self, lawyer_id: int) -> dict:
        lawyer = await self.db.get(Lawyer, lawyer_id)
        if not lawyer:
            return {"city_rank": 0, "city_total": 0, "domain_rank": 0, "domain_total": 0, "gap_to_next": None}

        city_total = await self.db.scalar(
            select(func.count(Lawyer.id)).where(Lawyer.city == lawyer.city, Lawyer.is_verified == True)
        )

        city_better = await self.db.scalar(
            select(func.count(Lawyer.id)).where(
                and_(Lawyer.city == lawyer.city, Lawyer.is_verified == True, Lawyer.rating > lawyer.rating)
            )
        )

        next_better = await self.db.execute(
            select(Lawyer.rating).where(
                and_(Lawyer.city == lawyer.city, Lawyer.is_verified == True, Lawyer.rating > lawyer.rating)
            ).order_by(Lawyer.rating.asc()).limit(1)
        )
        next_rating = next_better.scalar_one_or_none()

        return {
            "city_rank": (city_better or 0) + 1,
            "city_total": city_total or 0,
            "domain_rank": (city_better or 0) + 1,
            "domain_total": city_total or 0,
            "gap_to_next": round(next_rating - lawyer.rating, 2) if next_rating else None,
        }

    async def get_firm_dashboard(self, firm_id: int) -> dict:
        lawyer_count = await self.db.scalar(
            select(func.count(Lawyer.id)).where(Lawyer.firm_id == firm_id)
        )

        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        month_cons = await self.db.scalar(
            select(func.count(Consultation.id)).where(
                and_(Consultation.lawyer_id.in_(
                    select(Lawyer.id).where(Lawyer.firm_id == firm_id)
                ), Consultation.created_at >= month_start)
            )
        )

        avg_rating = await self.db.scalar(
            select(func.avg(Lawyer.rating)).where(Lawyer.firm_id == firm_id)
        )

        ranking_result = await self.db.execute(
            select(Lawyer.id, Lawyer.name, Lawyer.rating, Lawyer.consultation_count)
            .where(Lawyer.firm_id == firm_id, Lawyer.is_verified == True)
            .order_by(Lawyer.rating.desc())
            .limit(10)
        )
        rankings = [
            {"lawyer_id": r[0], "name": r[1], "rating": round(r[2], 1) if r[2] else 0, "consultations": r[3]}
            for r in ranking_result.all()
        ]

        return {
            "lawyer_count": lawyer_count or 0,
            "month_consultations": month_cons or 0,
            "avg_rating": round(avg_rating, 1) if avg_rating else 0.0,
            "ranking": rankings,
        }