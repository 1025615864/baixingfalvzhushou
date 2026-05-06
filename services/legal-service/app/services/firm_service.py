"""律所服务"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..models import LawFirm, LawFirmVerification, LawFirmAdmin, Lawyer, LawFirmInvitation
from ..shared.firm_state_machine import (
    FirmStatus,
    FirmStateMachine,
    FIRM_TRANSITIONS,
)
from ..shared.state_machines import TransitionError
from ..cache.lawyer_cache import FirmCache


class FirmService:
    """律所服务"""

    def __init__(self, db: AsyncSession, cache: FirmCache = None):
        self.db = db
        self.cache = cache

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
        status: Optional[str] = "verified",
    ) -> tuple[List[LawFirm], int]:
        """获取律所列表"""
        query = select(LawFirm)

        if status:
            query = query.where(LawFirm.status == status)
        if province:
            query = query.where(LawFirm.province == province)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        firms = result.scalars().all()

        return list(firms), total

    async def create_firm(
        self,
        user_id: int,
        name: str,
        license_no: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        description: Optional[str] = None,
    ) -> LawFirm:
        """创建律所（入驻申请）"""
        firm = LawFirm(
            user_id=user_id,
            name=name,
            license_no=license_no,
            province=province,
            city=city,
            address=address,
            phone=phone,
            email=email,
            description=description,
            status=FirmStatus.PENDING.value,
        )
        self.db.add(firm)
        await self.db.commit()
        await self.db.refresh(firm)

        if self.cache:
            await self.cache.invalidate_firm_list()

        return firm

    async def submit_verification(
        self,
        firm_id: int,
        license_image: Optional[str] = None,
        id_card_image: Optional[str] = None,
    ) -> LawFirmVerification:
        """提交资质审核"""
        firm = await self.get_firm(firm_id)
        if not firm:
            raise ValueError("律所不存在")

        if not FirmStateMachine.can_transition_from(firm.status, FirmStatus.UNDER_REVIEW.value):
            raise TransitionError(
                current_state=firm.status,
                target_state=FirmStatus.UNDER_REVIEW.value,
            )

        verification = LawFirmVerification(
            lawfirm_id=firm_id,
            license_image=license_image,
            id_card_image=id_card_image,
            status="pending",
        )
        self.db.add(verification)

        firm.status = FirmStatus.UNDER_REVIEW.value

        await self.db.commit()
        await self.db.refresh(verification)

        if self.cache:
            await self.cache.invalidate_firm_detail(firm_id)

        return verification

    async def get_verification_status(self, firm_id: int) -> Optional[LawFirmVerification]:
        """获取律所审核状态"""
        result = await self.db.execute(
            select(LawFirmVerification).where(
                LawFirmVerification.lawfirm_id == firm_id
            ).order_by(LawFirmVerification.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def approve_firm(
        self,
        firm_id: int,
        reviewed_by_user_id: int,
    ) -> LawFirm:
        """审核通过律所"""
        firm = await self.get_firm(firm_id)
        if not firm:
            raise ValueError("律所不存在")

        if not FirmStateMachine.can_transition_from(firm.status, FirmStatus.APPROVED.value):
            raise TransitionError(
                current_state=firm.status,
                target_state=FirmStatus.APPROVED.value,
            )

        firm.status = FirmStatus.APPROVED.value

        verification = await self.get_verification_status(firm_id)
        if verification:
            verification.status = "approved"
            verification.reviewed_by_user_id = reviewed_by_user_id
            verification.reviewed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(firm)

        if self.cache:
            await self.cache.invalidate_firm_detail(firm_id)
            await self.cache.invalidate_firm_list()

        return firm

    async def reject_firm(
        self,
        firm_id: int,
        reviewed_by_user_id: int,
        reason: str,
    ) -> LawFirm:
        """审核拒绝律所"""
        firm = await self.get_firm(firm_id)
        if not firm:
            raise ValueError("律所不存在")

        if not FirmStateMachine.can_transition_from(firm.status, FirmStatus.REJECTED.value):
            raise TransitionError(
                current_state=firm.status,
                target_state=FirmStatus.REJECTED.value,
            )

        firm.status = FirmStatus.REJECTED.value

        verification = await self.get_verification_status(firm_id)
        if verification:
            verification.status = "rejected"
            verification.rejection_reason = reason
            verification.reviewed_by_user_id = reviewed_by_user_id
            verification.reviewed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(firm)

        if self.cache:
            await self.cache.invalidate_firm_detail(firm_id)
            await self.cache.invalidate_firm_list()

        return firm

    async def get_firm_lawyers(
        self,
        firm_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Lawyer], int]:
        """获取律所的律师列表"""
        query = select(Lawyer).where(Lawyer.lawfirm_id == firm_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Lawyer.consultation_count.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        lawyers = result.scalars().all()

        return list(lawyers), total

    async def add_firm_admin(
        self,
        firm_id: int,
        user_id: int,
        role: str = "admin",
    ) -> LawFirmAdmin:
        """添加律所管理员"""
        admin = LawFirmAdmin(
            lawfirm_id=firm_id,
            user_id=user_id,
            role=role,
        )
        self.db.add(admin)
        await self.db.commit()
        await self.db.refresh(admin)
        return admin

    async def is_firm_admin(self, firm_id: int, user_id: int) -> bool:
        """检查用户是否是律所管理员"""
        result = await self.db.execute(
            select(LawFirmAdmin).where(
                and_(
                    LawFirmAdmin.lawfirm_id == firm_id,
                    LawFirmAdmin.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def update_firm(
        self,
        firm_id: int,
        **kwargs,
    ) -> Optional[LawFirm]:
        """更新律所信息"""
        firm = await self.get_firm(firm_id)
        if not firm:
            return None

        for key, value in kwargs.items():
            if hasattr(firm, key) and value is not None:
                setattr(firm, key, value)

        firm.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(firm)

        if self.cache:
            await self.cache.invalidate_firm_detail(firm_id)

        return firm

    async def suspend_firm(
        self,
        firm_id: int,
        reason: Optional[str] = None,
    ) -> LawFirm:
        """暂停律所"""
        firm = await self.get_firm(firm_id)
        if not firm:
            raise ValueError("律所不存在")

        if not FirmStateMachine.can_transition_from(firm.status, FirmStatus.SUSPENDED.value):
            raise TransitionError(
                current_state=firm.status,
                target_state=FirmStatus.SUSPENDED.value,
            )

        firm.status = FirmStatus.SUSPENDED.value
        firm.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(firm)

        if self.cache:
            await self.cache.invalidate_firm_detail(firm_id)
            await self.cache.invalidate_firm_list()

        return firm

    async def deactivate_firm(
        self,
        firm_id: int,
        reason: Optional[str] = None,
    ) -> LawFirm:
        """注销律所"""
        firm = await self.get_firm(firm_id)
        if not firm:
            raise ValueError("律所不存在")

        if not FirmStateMachine.can_transition_from(firm.status, FirmStatus.DEACTIVATED.value):
            raise TransitionError(
                current_state=firm.status,
                target_state=FirmStatus.DEACTIVATED.value,
            )

        firm.status = FirmStatus.DEACTIVATED.value
        firm.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(firm)

        if self.cache:
            await self.cache.invalidate_firm_detail(firm_id)
            await self.cache.invalidate_firm_list()

        return firm