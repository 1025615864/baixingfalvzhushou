"""律师服务"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from ..models import Lawyer
from ..cache.lawyer_cache import LawyerCache


class LawyerService:
    """律师服务"""

    def __init__(self, db: AsyncSession, cache: LawyerCache = None):
        self.db = db
        self.cache = cache

    async def get_lawyer(self, lawyer_id: int) -> Optional[Lawyer]:
        """获取律师"""
        result = await self.db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> Optional[Lawyer]:
        """通过用户ID获取律师"""
        result = await self.db.execute(
            select(Lawyer).where(Lawyer.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_lawyers(
        self,
        page: int = 1,
        page_size: int = 20,
        specialty: Optional[str] = None,
        city: Optional[str] = None,
        min_rating: Optional[float] = None,
    ) -> tuple[List[Lawyer], int]:
        """获取律师列表"""
        query = select(Lawyer).where(Lawyer.status == "verified")

        if specialty:
            query = query.where(Lawyer.specialties.contains([specialty]))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Lawyer.rating.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        lawyers = result.scalars().all()

        return list(lawyers), total

    async def search_lawyers(
        self,
        specialty: Optional[str] = None,
        city: Optional[str] = None,
        min_rating: Optional[float] = None,
        available: Optional[bool] = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Lawyer], int]:
        """搜索律师"""
        query = select(Lawyer).where(Lawyer.status == "verified")

        if specialty:
            query = query.where(Lawyer.specialties.contains([specialty]))

        if min_rating is not None:
            query = query.where(Lawyer.rating >= min_rating)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Lawyer.rating.desc(), Lawyer.consultation_count.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        lawyers = result.scalars().all()

        return list(lawyers), total

    async def update_profile(
        self,
        lawyer_id: int,
        profile_data: dict,
    ) -> Optional[Lawyer]:
        """更新律师资料"""
        lawyer = await self.get_lawyer(lawyer_id)
        if not lawyer:
            return None

        for key, value in profile_data.items():
            if hasattr(lawyer, key) and value is not None:
                setattr(lawyer, key, value)

        lawyer.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(lawyer)

        if self.cache:
            await self.cache.invalidate_lawyer_detail(lawyer_id)
            await self.cache.invalidate_lawyer_list()

        return lawyer

    async def verify(self, lawyer_id: int) -> dict:
        """认证律师"""
        lawyer = await self.get_lawyer(lawyer_id)
        if not lawyer:
            raise ValueError("Lawyer not found")

        lawyer.status = "verified"
        lawyer.verified_at = datetime.utcnow()
        await self.db.commit()

        if self.cache:
            await self.cache.invalidate_lawyer_detail(lawyer_id)
            await self.cache.invalidate_lawyer_list()

        return {
            "id": lawyer.id,
            "name": lawyer.name,
            "status": lawyer.status,
            "verified_at": lawyer.verified_at,
        }

    async def update_rating(self, lawyer_id: int, new_rating: float) -> Optional[Lawyer]:
        """更新律师评分"""
        lawyer = await self.get_lawyer(lawyer_id)
        if not lawyer:
            return None

        lawyer.rating = new_rating
        lawyer.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(lawyer)

        if self.cache:
            await self.cache.invalidate_lawyer_detail(lawyer_id)
            await self.cache.invalidate_lawyer_list()

        return lawyer

    async def increment_consultation_count(self, lawyer_id: int) -> Optional[Lawyer]:
        """增加咨询计数"""
        lawyer = await self.get_lawyer(lawyer_id)
        if not lawyer:
            return None

        lawyer.consultation_count = (lawyer.consultation_count or 0) + 1
        lawyer.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(lawyer)

        if self.cache:
            await self.cache.invalidate_lawyer_detail(lawyer_id)

        return lawyer