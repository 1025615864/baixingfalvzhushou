"""认证路由"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.models.verification import LawyerVerification

logger = logging.getLogger(__name__)
router = APIRouter()


class OCRSubmitRequest(BaseModel):
    image_url: str


class AnnualCheckRequest(BaseModel):
    force: bool = False


@router.get("/lawyers/verification/status")
async def get_verification_status(user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LawyerVerification)
        .where(LawyerVerification.user_id == user_id)
        .order_by(LawyerVerification.created_at.desc())
    )
    verification = result.scalars().first()
    if not verification:
        return {"status": "not_submitted"}
    return verification


@router.post("/lawyers/verification/submit")
async def submit_verification(
    user_id: int = Query(...),
    real_name: str = "",
    id_card_no: str = "",
    license_no: str = "",
    firm_name: str = "",
    specialties: str = "",
    introduction: str = "",
    experience_years: int = 0,
    license_image: Optional[str] = None,
    expires_at: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(LawyerVerification)
        .where(LawyerVerification.user_id == user_id)
        .where(LawyerVerification.status == "pending")
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="已有待审核的认证申请")

    parsed_expires_at = None
    if expires_at:
        try:
            parsed_expires_at = datetime.fromisoformat(expires_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="expires_at 格式错误")

    verification = LawyerVerification(
        user_id=user_id,
        real_name=real_name,
        id_card_no=id_card_no,
        license_no=license_no,
        firm_name=firm_name,
        specialties=specialties,
        introduction=introduction,
        experience_years=experience_years,
        license_image=license_image,
        expires_at=parsed_expires_at,
        status="pending",
    )
    db.add(verification)
    await db.commit()
    await db.refresh(verification)
    return verification


@router.post("/lawyers/verification/ocr-submit")
async def ocr_submit_verification(
    user_id: int = Query(...),
    image_url: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """OCR 识别执业证并自动填充提交认证申请"""
    import httpx

    existing = await db.execute(
        select(LawyerVerification)
        .where(LawyerVerification.user_id == user_id)
        .where(LawyerVerification.status == "pending")
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="已有待审核的认证申请")

    ocr_data = {}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "http://ai-service:8005/api/v1/ai/ocr/extract-lawyer-license",
                json={"image_url": image_url, "cert_type": "lawyer_license"},
            )
            if resp.status_code == 200:
                result = resp.json()
                if result.get("success") and result.get("data"):
                    ocr_data = result["data"]
    except Exception as e:
        logger.warning(f"OCR 识别失败: {e}")

    parsed_expires_at = None
    if ocr_data.get("annual_check_date"):
        try:
            parsed_expires_at = datetime.fromisoformat(ocr_data["annual_check_date"])
        except (ValueError, TypeError):
            pass

    verification = LawyerVerification(
        user_id=user_id,
        real_name=ocr_data.get("name", ""),
        license_no=ocr_data.get("license_no", ""),
        firm_name=ocr_data.get("law_firm", ""),
        license_image=image_url,
        expires_at=parsed_expires_at,
        status="pending",
    )
    db.add(verification)
    await db.commit()
    await db.refresh(verification)

    return {
        "verification": verification,
        "ocr_result": ocr_data,
        "auto_filled": len(ocr_data) > 0,
    }


@router.put("/lawyers/verification/{verification_id}/review")
async def review_verification(
    verification_id: int,
    status: str = "approved",
    reject_reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LawyerVerification).where(LawyerVerification.id == verification_id)
    )
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="认证申请不存在")
    verification.status = status
    if reject_reason:
        verification.reject_reason = reject_reason
    verification.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "审核完成", "status": status}


@router.get("/lawyers/verification/annual-check")
async def check_annual_inspection(
    lawyer_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """检查律师年检状态"""
    from ..services.verification_service import VerificationService

    service = VerificationService(db)
    result = await service.check_annual_inspection(lawyer_id)
    return result


@router.post("/lawyers/verification/annual-check/run")
async def run_annual_inspection_batch(
    db: AsyncSession = Depends(get_db),
):
    """批量运行年检检查（管理员/定时任务调用）"""
    from ..services.verification_service import VerificationService

    service = VerificationService(db)
    result = await service.run_annual_check_batch()
    return result


@router.post("/lawyers/verification/{verification_id}/renew")
async def renew_verification(
    verification_id: int,
    new_expires_at: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """更新年检到期日期"""
    result = await db.execute(
        select(LawyerVerification).where(LawyerVerification.id == verification_id)
    )
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="认证记录不存在")

    try:
        verification.expires_at = datetime.fromisoformat(new_expires_at)
    except ValueError:
        raise HTTPException(status_code=400, detail="new_expires_at 格式错误")

    if verification.status == "expired":
        verification.status = "approved"

    await db.commit()
    return {"message": "年检已更新", "expires_at": new_expires_at, "status": verification.status}