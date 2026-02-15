"""Lawyer services - 律师管理服务"""
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_, update
from sqlalchemy.orm import selectinload

from app.models.lawfirm import Lawyer
from app.schemas.lawfirm import LawyerCreate, LawyerUpdate


class LawyerService:
    """律师服务"""

    @staticmethod
    async def create(db: AsyncSession, data: LawyerCreate,
                     user_id: int | None = None) -> Lawyer:
        """创建律师"""
        lawyer = Lawyer(**data.model_dump(), user_id=user_id)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        return lawyer

    @staticmethod
    async def get_by_id(db: AsyncSession, lawyer_id: int) -> Lawyer | None:
        """获取律师"""
        result = await db.execute(
            select(Lawyer)
            .options(selectinload(Lawyer.firm))
            .where(Lawyer.id == lawyer_id, Lawyer.is_active)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: int) -> Lawyer | None:
        """通过用户ID获取律师"""
        result = await db.execute(
            select(Lawyer).where(Lawyer.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        firm_id: int | None = None,
        city: str | None = None,
        specialty: str | None = None,
        keyword: str | None = None
    ) -> tuple[list[Lawyer], int]:
        """获取律师列表"""
        query = select(Lawyer).where(Lawyer.is_active)
        count_query = select(
            func.count(
                Lawyer.id)).where(
            Lawyer.is_active)

        if firm_id:
            query = query.where(Lawyer.firm_id == firm_id)
            count_query = count_query.where(Lawyer.firm_id == firm_id)

        if city:
            query = query.where(Lawyer.specialties.contains(city))
            count_query = count_query.where(Lawyer.specialties.contains(city))

        if specialty:
            query = query.where(Lawyer.specialties.contains(specialty))
            count_query = count_query.where(
                Lawyer.specialties.contains(specialty))

        if keyword:
            search_filter = or_(
                Lawyer.name.contains(keyword),
                Lawyer.title.contains(keyword)
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        query = query.order_by(desc(Lawyer.case_count), desc(Lawyer.rating))
        query = query.options(selectinload(Lawyer.firm))  # 预加载律所关联，避免 N+1 查询
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        lawyers = result.scalars().all()

        count_result = await db.execute(count_query)
        total = int(count_result.scalar() or 0)

        return list(lawyers), total

    @staticmethod
    async def update(db: AsyncSession, lawyer: Lawyer,
                     data: LawyerUpdate) -> Lawyer:
        """更新律师"""
        update_data: dict[str, object] = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lawyer, field, value)
        await db.commit()
        await db.refresh(lawyer)
        return lawyer

    @staticmethod
    async def increment_consultation_count(
            db: AsyncSession, lawyer_id: int) -> None:
        """增加咨询次数"""
        await db.execute(
            update(Lawyer)
            .where(Lawyer.id == lawyer_id)
            .values(case_count=Lawyer.case_count + 1)
        )
        await db.commit()

    @staticmethod
    async def update_rating(db: AsyncSession, lawyer_id: int) -> None:
        """更新律师评分"""
        from app.models.lawfirm import LawyerReview
        from sqlalchemy import select, func

        result = await db.execute(
            select(
                func.avg(LawyerReview.rating),
                func.count(LawyerReview.id)
            ).where(LawyerReview.lawyer_id == lawyer_id)
        )
        row = result.one()
        avg_rating = row[0] or 0.0
        review_count = row[1] or 0

        lawyer_result = await db.execute(select(Lawyer).where(Lawyer.id == lawyer_id))
        lawyer = lawyer_result.scalar_one_or_none()
        if lawyer:
            lawyer.rating = round(float(avg_rating), 1)
            lawyer.review_count = review_count
            await db.commit()

    @staticmethod
    async def get_ranking(
        db: AsyncSession,
        limit: int = 10,
        period: str | None = None,
    ) -> list[dict[str, Any]]:
        """获取律师排行榜"""
        query = select(Lawyer).where(Lawyer.is_active)
        query = query.order_by(desc(Lawyer.rating), desc(Lawyer.case_count))
        query = query.limit(limit)

        result = await db.execute(query)
        lawyers = result.scalars().all()

        return [
            {
                "id": l.id,
                "name": l.name,
                "title": l.title,
                "specialties": l.specialties,
                "rating": l.rating,
                "case_count": l.case_count,
                "review_count": l.review_count,
            }
            for l in lawyers
        ]
