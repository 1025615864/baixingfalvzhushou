"""Lawyer review services - 律师评价服务"""
from datetime import datetime
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, case

from app.models.lawfirm import LawyerReview


class ReviewService:
    """律师评价服务"""

    @staticmethod
    async def create(
        db: AsyncSession,
        consultation_id: int,
        lawyer_id: int,
        user_id: int,
        rating: int,
        content: str | None = None,
        dimensions: dict | None = None
    ) -> LawyerReview:
        """创建评价"""
        # 将多维度评价转换为标签存储
        tags = None
        if dimensions:
            import json
            tags = json.dumps(dimensions, ensure_ascii=False)

        review = LawyerReview(
            consultation_id=consultation_id,
            lawyer_id=lawyer_id,
            user_id=user_id,
            rating=rating,
            content=content,
            tags=tags,
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        review_id: int
    ) -> LawyerReview | None:
        """获取评价"""
        result = await db.execute(
            select(LawyerReview).where(LawyerReview.id == review_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_lawyer_reviews(
        db: AsyncSession,
        lawyer_id: int,
        page: int = 1,
        page_size: int = 20,
        min_rating: int | None = None
    ) -> tuple[list[LawyerReview], int]:
        """获取律师的评价列表"""
        query = select(LawyerReview).where(LawyerReview.lawyer_id == lawyer_id)
        count_query = select(func.count(LawyerReview.id)).where(
            LawyerReview.lawyer_id == lawyer_id
        )

        if min_rating:
            query = query.where(LawyerReview.rating >= min_rating)
            count_query = count_query.where(LawyerReview.rating >= min_rating)

        query = query.order_by(desc(LawyerReview.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        reviews = result.scalars().all()

        count_result = await db.execute(count_query)
        total = int(count_result.scalar() or 0)

        return list(reviews), total

    @staticmethod
    async def get_by_lawyer(
        db: AsyncSession,
        lawyer_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LawyerReview], int]:
        """获取律师的评价列表 (别名)"""
        return await ReviewService.get_lawyer_reviews(db, lawyer_id, page, page_size)

    @staticmethod
    async def get_average_rating(
        db: AsyncSession,
        lawyer_id: int
    ) -> dict:
        """获取律师的平均评分"""
        result = await db.execute(
            select(
                func.avg(LawyerReview.rating).label("avg_rating"),
                func.count(LawyerReview.id).label("total_count")
            ).where(LawyerReview.lawyer_id == lawyer_id)
        )
        row = result.one()

        # 计算各维度平均分
        dimension_stats = {}
        dimensions = ["professionalism", "responsiveness", "attitude"]

        for dim in dimensions:
            dim_result = await db.execute(
                select(
                    func.avg(
                        case(
                            (getattr(LawyerReview, dim).isnot(
                                None), getattr(LawyerReview, dim)),
                            else_=None
                        )
                    ).label(f"avg_{dim}")
                ).where(
                    LawyerReview.lawyer_id == lawyer_id,
                    getattr(LawyerReview, dim).isnot(None)
                )
            )
            dim_row = dim_result.one()
            if dim_row[0]:
                dimension_stats[dim] = round(float(dim_row[0]), 1)

        return {
            "average_rating": round(
                float(
                    row.avg_rating or 0),
                1) if row.avg_rating else None,
            "total_count": row.total_count or 0,
            "dimension_ratings": dimension_stats}

    @staticmethod
    async def get_summary(db: AsyncSession, lawyer_id: int) -> dict[str, Any]:
        """获取律师评价摘要"""
        # 获取平均评分
        avg_result = await db.execute(
            select(
                func.avg(LawyerReview.rating).label("avg_rating"),
                func.count(LawyerReview.id).label("total_count")
            ).where(LawyerReview.lawyer_id == lawyer_id)
        )
        avg_row = avg_result.one()

        # 获取评分分布
        dist_result = await db.execute(
            select(
                LawyerReview.rating,
                func.count(LawyerReview.id)
            ).where(
                LawyerReview.lawyer_id == lawyer_id
            ).group_by(LawyerReview.rating)
        )
        distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        for row in dist_result.all():
            distribution[str(row[0])] = row[1]

        # 获取标签统计
        tag_stats_result = await db.execute(
            select(LawyerReview.tags, func.count(LawyerReview.id))
            .where(LawyerReview.lawyer_id == lawyer_id, LawyerReview.tags.isnot(None))
            .group_by(LawyerReview.tags)
            .order_by(func.count(LawyerReview.id).desc())
            .limit(10)
        )
        tag_stats = [{"tag": row[0] or "未分类", "count": row[1]}
                     for row in tag_stats_result.all()]

        # 获取维度统计
        dimension_stats_result = await db.execute(
            select(
                func.avg(LawyerReview.professionalism).label(
                    "professionalism"),
                func.avg(LawyerReview.responsiveness).label("responsiveness"),
                func.avg(LawyerReview.attitude).label("attitude")
            ).where(LawyerReview.lawyer_id == lawyer_id)
        )
        dim_row = dimension_stats_result.one()
        dimension_stats = {
            "professionalism": round(float(dim_row[0] or 0), 1),
            "responsiveness": round(float(dim_row[1] or 0), 1),
            "attitude": round(float(dim_row[2] or 0), 1),
        }

        return {
            "total": avg_row.total_count or 0,
            "avg_rating": round(float(avg_row.avg_rating or 0), 1),
            "distribution": distribution,
            "tag_stats": tag_stats,
            "dimension_stats": dimension_stats,
        }
