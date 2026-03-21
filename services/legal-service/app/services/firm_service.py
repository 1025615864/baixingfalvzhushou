"""律所服务"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import LawFirm


class FirmService:
    """律所服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_firm(self, firm_id: int) -> Optional[LawFirm]:
        """获取律所"""
        result = await self.db.execute(
            select(LawFirm).where(LawFirm.id == firm_id)
        )
        return result.scalar_one_or_none()

    async def list_firms(
        self,
        page: int = 1,
        page_size: int = 20,
        province: Optional[str] = None,
    ) -> tuple[List[LawFirm], int]:
        """获取律所列表"""
        query = select(LawFirm).where(LawFirm.status == "verified")

        if province:
            query = query.where(LawFirm.province == province)

        total_result = await self.db.execute(query)
        total = len(total_result.scalars().all())

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        firms = result.scalars().all()

        return list(firms), total
