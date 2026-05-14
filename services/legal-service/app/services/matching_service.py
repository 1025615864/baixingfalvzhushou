"""智能匹配服务"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from ..models import Lawyer, LawyerSchedule, Consultation


class MatchingService:
    """智能律师匹配服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def match_for_consultation(
        self,
        consultation_id: int,
        limit: int = 5,
    ) -> List[dict]:
        """为咨询匹配最佳律师"""
        consultation_result = await self.db.execute(
            select(Consultation).where(Consultation.id == consultation_id)
        )
        consultation = consultation_result.scalar_one_or_none()
        if not consultation:
            return []

        lawyers_result = await self.db.execute(
            select(Lawyer).where(
                and_(
                    Lawyer.status == "verified",
                    Lawyer.city == consultation.city,
                )
            ).order_by(Lawyer.rating.desc(), Lawyer.response_time.asc())
            .limit(limit * 2)
        )
        all_lawyers = lawyers_result.scalars().all()

        matched = []
        for lawyer in all_lawyers:
            score = self._calculate_match_score(lawyer, consultation)
            matched.append({
                "lawyer_id": lawyer.id,
                "name": lawyer.name,
                "title": lawyer.title,
                "specialties": lawyer.specialties or [],
                "rating": lawyer.rating,
                "city": lawyer.city,
                "score": score,
                "is_available_today": await self._check_availability(lawyer.id),
            })

        matched.sort(key=lambda x: (-x["score"], x["lawyer_id"]))
        return matched[:limit]

    async def match_by_specialty(
        self,
        category: str,
        city: Optional[str] = None,
        limit: int = 10,
    ) -> List[dict]:
        """按专业领域匹配律师"""
        query = select(Lawyer).where(
            and_(
                Lawyer.status == "verified",
                Lawyer.specialties.contains([category]),
            )
        )

        if city:
            query = query.where(Lawyer.city == city)

        query = query.order_by(Lawyer.rating.desc()).limit(limit)
        result = await self.db.execute(query)
        lawyers = result.scalars().all()

        return [
            {
                "lawyer_id": l.id,
                "name": l.name,
                "title": l.title,
                "specialties": l.specialties or [],
                "rating": l.rating,
                "city": l.city,
            }
            for l in lawyers
        ]

    async def match_by_keywords(
        self,
        keywords: List[str],
        city: Optional[str] = None,
        limit: int = 10,
    ) -> List[dict]:
        """按关键词匹配律师"""
        conditions = []
        for kw in keywords:
            conditions.append(Lawyer.bio.contains(kw))
            conditions.append(Lawyer.title.contains(kw))
            conditions.append(Lawyer.specialties.contains([kw]))

        query = select(Lawyer).where(
            and_(
                Lawyer.status == "verified",
                or_(*conditions) if conditions else True,
            )
        )

        if city:
            query = query.where(Lawyer.city == city)

        query = query.order_by(Lawyer.rating.desc()).limit(limit)
        result = await self.db.execute(query)
        lawyers = result.scalars().all()

        return [
            {
                "lawyer_id": l.id,
                "name": l.name,
                "title": l.title,
                "specialties": l.specialties or [],
                "rating": l.rating,
                "city": l.city,
            }
            for l in lawyers
        ]

    def _calculate_match_score(self, lawyer: Lawyer, consultation: Consultation) -> float:
        """计算匹配分数"""
        score = 0.0

        score += lawyer.rating * 2.0

        if lawyer.consultation_count:
            score += min(lawyer.consultation_count * 0.1, 10.0)

        if lawyer.city == consultation.city:
            score += 5.0

        specialty_match = 0
        if consultation.category in (lawyer.specialties or []):
            specialty_match = 3.0
            score += specialty_match

        return round(score, 2)

    async def _check_availability(self, lawyer_id: int) -> bool:
        """检查律师今天是否可用"""
        today = datetime.now(timezone.utc).date()
        tomorrow = datetime.combine(today, datetime.max.time())

        result = await self.db.execute(
            select(func.count(LawyerSchedule.id)).where(
                and_(
                    LawyerSchedule.lawyer_id == lawyer_id,
                    LawyerSchedule.date >= datetime.combine(today, datetime.min.time()),
                    LawyerSchedule.date <= tomorrow,
                    LawyerSchedule.is_available == True,
                )
            )
        )
        count = result.scalar() or 0
        return count > 0

    async def get_recommended_lawyers(
        self,
        user_id: int,
        limit: int = 5,
    ) -> List[dict]:
        """获取推荐律师（基于历史咨询）"""
        result = await self.db.execute(
            select(
                Consultation.category,
                func.count(Consultation.id).label("count"),
            ).where(
                Consultation.user_id == user_id
            ).group_by(Consultation.category).order_by(func.count(Consultation.id).desc())
        )
        categories = result.all()

        if not categories:
            return await self.match_by_specialty(
                category="婚姻继承",
                limit=limit,
            )

        recommended = []
        for cat_row in categories[:3]:
            lawyers = await self.match_by_specialty(cat_row.category, limit=3)
            recommended.extend(lawyers)

        seen = set()
        unique = []
        for l in recommended:
            if l["lawyer_id"] not in seen:
                seen.add(l["lawyer_id"])
                unique.append(l)

        return unique[:limit]