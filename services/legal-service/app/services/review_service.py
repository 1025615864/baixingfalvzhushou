"""评价服务"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models import Review, Consultation, Lawyer
from ..cache.lawyer_cache import LawyerCache


class ReviewService:
    """评价服务"""

    def __init__(self, db: AsyncSession, cache: LawyerCache = None):
        self.db = db
        self.cache = cache

    async def create(
        self,
        consultation_id: int,
        lawyer_id: int,
        user_id: int,
        rating: int,
        content: Optional[str] = None,
        is_anonymous: bool = False,
    ) -> Review:
        """创建评价"""
        review = Review(
            consultation_id=consultation_id,
            lawyer_id=lawyer_id,
            user_id=user_id,
            rating=rating,
            content=content,
            is_anonymous=is_anonymous,
        )
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)

        await self._update_lawyer_rating(lawyer_id)

        return review

    async def get_by_consultation(self, consultation_id: int) -> Optional[Review]:
        """获取咨询的评价"""
        result = await self.db.execute(
            select(Review).where(Review.consultation_id == consultation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_lawyer(
        self,
        lawyer_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Review], int]:
        """获取律师的所有评价"""
        query = select(Review).where(Review.lawyer_id == lawyer_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Review.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        reviews = result.scalars().all()

        return list(reviews), total

    async def get_lawyer_stats(self, lawyer_id: int) -> dict:
        """获取律师评分统计"""
        result = await self.db.execute(
            select(
                func.count(Review.id).label("total"),
                func.avg(Review.rating).label("avg_rating"),
            ).where(Review.lawyer_id == lawyer_id)
        )
        row = result.one()

        return {
            "total": row.total or 0,
            "avg_rating": round(row.avg_rating, 1) if row.avg_rating else 5.0,
        }

    async def _update_lawyer_rating(self, lawyer_id: int) -> None:
        """更新律师评分"""
        result = await self.db.execute(
            select(
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("count"),
            ).where(Review.lawyer_id == lawyer_id)
        )
        row = result.one()

        lawyer_result = await self.db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        lawyer = lawyer_result.scalar_one_or_none()
        if lawyer:
            lawyer.rating = round(row.avg_rating, 1) if row.avg_rating else 5.0
            lawyer.rating_count = row.count or 0
            await self.db.commit()

            if self.cache:
                await self.cache.invalidate_lawyer_detail(lawyer_id)
                await self.cache.invalidate_lawyer_list()