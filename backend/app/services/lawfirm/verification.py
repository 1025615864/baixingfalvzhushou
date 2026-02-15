"""律师认证服务"""
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.lawfirm import LawyerVerification
from app.schemas.lawfirm import VerificationCreate


class LawyerVerificationService:
    """律师认证服务"""

    @staticmethod
    def _validate_id_card_no(id_card_no: str) -> Tuple[bool, str]:
        """校验身份证号"""
        import re
        if not re.match(r"^\d{17}[\dXx]$", id_card_no):
            return False, "身份证号格式不正确"
        return True, ""

    @staticmethod
    def _validate_license_no(license_no: str) -> Tuple[bool, str]:
        """校验执业证号"""
        import re
        if not re.match(r"^[\dA-Za-z]{10,20}$", license_no):
            return False, "执业证号格式不正确"
        return True, ""

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        data: VerificationCreate,
    ) -> LawyerVerification:
        """创建认证申请"""
        # 验证身份证号
        is_valid_id, id_error = LawyerVerificationService._validate_id_card_no(
            data.id_card_no)
        if not is_valid_id:
            raise ValueError(id_error)

        # 验证执业证号
        is_valid_license, license_error = LawyerVerificationService._validate_license_no(
            data.license_no)
        if not is_valid_license:
            raise ValueError(license_error)

        # 检查是否已有认证申请
        existing = await db.execute(
            select(LawyerVerification).where(
                LawyerVerification.user_id == user_id
            )
        )
        existing_verification = existing.scalar_one_or_none()

        if existing_verification:
            if existing_verification.status == "approved":
                raise ValueError("律师已完成认证")
            elif existing_verification.status == "pending":
                raise ValueError("已有待审核的认证申请")
            elif existing_verification.status == "rejected":
                # 允许重新提交被拒绝的申请
                pass

        verification = LawyerVerification(
            user_id=user_id,
            real_name=data.real_name,
            id_card_no=data.id_card_no,
            license_no=data.license_no,
            license_photo=data.license_photo,
            id_card_front=data.id_card_front,
            id_card_back=data.id_card_back,
            firm_name=data.firm_name,
            specialties=data.specialties,
            introduction=data.introduction,
            experience_years=data.experience_years,
            status="pending",
        )
        db.add(verification)
        await db.commit()
        await db.refresh(verification)
        return verification

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        verification_id: int,
    ) -> Optional[LawyerVerification]:
        """根据ID获取认证申请"""
        result = await db.execute(
            select(LawyerVerification).where(
                LawyerVerification.id == verification_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user_id(
        db: AsyncSession,
        user_id: int,
    ) -> Optional[LawyerVerification]:
        """根据用户ID获取认证申请"""
        result = await db.execute(
            select(LawyerVerification).where(
                LawyerVerification.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[List[LawyerVerification], int]:
        """获取认证申请列表"""
        query = select(LawyerVerification)
        count_query = select(func.count(LawyerVerification.id))

        if status:
            query = query.where(LawyerVerification.status == status)
            count_query = count_query.where(
                LawyerVerification.status == status)

        query = query.order_by(LawyerVerification.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        verifications = result.scalars().all()

        count_result = await db.execute(count_query)
        total = int(count_result.scalar() or 0)

        return list(verifications), total

    @staticmethod
    async def approve(
        db: AsyncSession,
        verification_id: int,
        admin_id: int,
    ) -> Optional[LawyerVerification]:
        """批准认证申请"""
        verification = await LawyerVerificationService.get_by_id(db, verification_id)
        if not verification:
            return None

        verification.status = "approved"
        verification.reviewed_by = admin_id
        verification.reviewed_at = datetime.now()

        await db.commit()
        await db.refresh(verification)
        return verification

    @staticmethod
    async def reject(
        db: AsyncSession,
        verification_id: int,
        admin_id: int,
        reason: str,
    ) -> Optional[LawyerVerification]:
        """拒绝认证申请"""
        verification = await LawyerVerificationService.get_by_id(db, verification_id)
        if not verification:
            return None

        verification.status = "rejected"
        verification.reviewed_by = admin_id
        verification.reviewed_at = datetime.now()
        verification.reject_reason = reason

        await db.commit()
        await db.refresh(verification)
        return verification

    @staticmethod
    async def delete(
        db: AsyncSession,
        verification_id: int,
    ) -> bool:
        """删除认证申请"""
        verification = await LawyerVerificationService.get_by_id(db, verification_id)
        if not verification:
            return False

        await db.delete(verification)
        await db.commit()
        return True
