"""律师服务"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import Lawyer


class LawyerService:
    """律师服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_lawyer(self, lawyer_id: int) -> Optional[Lawyer]:
        """获取律师"""
        result = await self.db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        return result.scalar_one_or_none()

    async def list_lawyers(
        self,
        page: int = 1,
        page_size: int = 20,
        specialty: Optional[str] = None,
    ) -> tuple[List[Lawyer], int]:
        """获取律师列表"""
        query = select(Lawyer).where(Lawyer.status == "verified")

        total_result = await self.db.execute(query)
        total = len(total_result.scalars().all())

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        lawyers = result.scalars().all()

        return list(lawyers), total

    async def verify(self, lawyer_id: int) -> dict:
        """认证律师"""
        lawyer = await self.get_lawyer(lawyer_id)
        if not lawyer:
            raise ValueError("Lawyer not found")

        lawyer.status = "verified"
        lawyer.verified_at = datetime.utcnow()
        await self.db.commit()

        return {
            "id": lawyer.id,
            "name": lawyer.name,
            "status": lawyer.status,
            "verified_at": lawyer.verified_at,
        }
