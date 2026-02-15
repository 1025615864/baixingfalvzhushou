"""Law firm services - 律所 CRUD 服务"""
from datetime import datetime, timezone  # pyright: ignore
from typing import Any  # pyright: ignore
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_  # pyright: ignore

from app.models.lawfirm import LawFirm, Lawyer  # pyright: ignore
from app.schemas.lawfirm import LawFirmCreate, LawFirmUpdate  # pyright: ignore


class LawFirmService:
    """律所服务"""

    @staticmethod
    async def create(db: AsyncSession, data: LawFirmCreate) -> LawFirm:  # pyright: ignore
        """创建律所"""
        firm = LawFirm(**data.model_dump())  # pyright: ignore
        db.add(firm)  # pyright: ignore
        await db.commit()
        await db.refresh(firm)  # pyright: ignore
        return firm  # pyright: ignore

    @staticmethod
    async def get_by_id(db: AsyncSession, firm_id: int) -> LawFirm | None:  # pyright: ignore
        """获取律所"""
        result = await db.execute(  # pyright: ignore
            select(LawFirm).where(
                LawFirm.id == firm_id,
                LawFirm.is_active)  # pyright: ignore
        )
        return result.scalar_one_or_none()  # pyright: ignore

    @staticmethod
    # pyright: ignore
    async def get_list(db: AsyncSession,
                       page: int = 1,
                       page_size: int = 20,
                       city: str | None = None,
                       keyword: str | None = None) -> tuple[list[LawFirm],
                                                            int]:
        """获取律所列表"""
        query = select(LawFirm).where(
            LawFirm.is_active)  # pyright: ignore
        count_query = select(func.count(LawFirm.id)).where(
            LawFirm.is_active)  # pyright: ignore

        if city:
            query = query.where(LawFirm.city == city)  # pyright: ignore
            count_query = count_query.where(
                LawFirm.city == city)  # pyright: ignore

        if keyword:
            search_filter = or_(
                LawFirm.name.contains(keyword),  # pyright: ignore
                LawFirm.specialties.contains(keyword)  # pyright: ignore
            )
            query = query.where(search_filter)  # pyright: ignore
            count_query = count_query.where(search_filter)  # pyright: ignore

        query = query.order_by(
            desc(
                LawFirm.is_verified), desc(
                LawFirm.rating))  # pyright: ignore
        # 注意：LawFirm.lawyers 使用 lazy="dynamic"，不支持 selectinload
        query = query.offset(
            (page - 1) * page_size).limit(page_size)  # pyright: ignore

        result = await db.execute(query)  # pyright: ignore
        firms = result.scalars().all()  # pyright: ignore

        count_result = await db.execute(count_query)  # pyright: ignore
        total = int(count_result.scalar() or 0)

        return list(firms), total  # pyright: ignore

    @staticmethod
    async def update(db: AsyncSession, firm_id: int, data: LawFirmUpdate) -> LawFirm | None:  # pyright: ignore
        """更新律所"""
        firm = await LawFirmService.get_by_id(db, firm_id)
        if not firm:
            return None
        update_data: dict[str, object] = data.model_dump(
            exclude_unset=True)  # pyright: ignore
        for field, value in update_data.items():  # pyright: ignore
            setattr(firm, field, value)  # pyright: ignore
        await db.commit()
        await db.refresh(firm)  # pyright: ignore
        return firm  # pyright: ignore

    @staticmethod
    async def get_lawyer_count(db: AsyncSession, firm_id: int) -> int:
        """获取律所律师数量"""
        result = await db.execute(  # pyright: ignore
            select(func.count(Lawyer.id)).where(  # pyright: ignore
                Lawyer.firm_id == firm_id, Lawyer.is_active  # pyright: ignore
            )  # pyright: ignore
        )
        return result.scalar() or 0

    @staticmethod
    async def delete(db: AsyncSession, firm_id: int) -> bool:
        """删除律所（软删除）"""
        firm = await LawFirmService.get_by_id(db, firm_id)
        if not firm:
            return False
        firm.is_active = False
        await db.commit()
        return True
