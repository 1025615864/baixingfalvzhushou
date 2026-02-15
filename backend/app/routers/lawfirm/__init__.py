"""律所服务路由模块

包含：律所管理、律师管理、咨询预约、评价系统、认证管理、
日程管理、工作台、回复模板、主页管理、推广链接等功能。
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...schemas.lawfirm import (
    LawFirmListResponse, LawFirmResponse,
    LawyerListResponse,
)
from ...services.lawfirm_service import lawfirm_service
from ...utils.deps import get_current_user

from .firms import router as firms_router
from .lawyers import router as lawyers_router
from .consultations import router as consultations_router
from .consultation_messages import router as consultation_messages_router
from .reviews import router as reviews_router
from .verification import router as verification_router
from .schedules import router as schedules_router
from .dashboard import router as dashboard_router
from .templates import router as templates_router
from .homepage import router as homepage_router
from .promotions import router as promotions_router

router = APIRouter(prefix="/lawfirm", tags=["律所服务"])

# 挂载子路由
router.include_router(firms_router)
router.include_router(lawyers_router)
router.include_router(consultations_router)
router.include_router(consultation_messages_router)
router.include_router(reviews_router)
router.include_router(verification_router)
router.include_router(schedules_router)
router.include_router(dashboard_router)
router.include_router(templates_router)
router.include_router(homepage_router)
router.include_router(promotions_router)


# 兼容前端路由：/lawfirm（对应 /lawfirm/firms）
@router.get("", response_model=LawFirmListResponse, summary="获取律所列表（兼容路由）")
async def get_law_firms_compat(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    keyword: str | None = None,
):
    """获取律所列表，兼容前端 /lawfirm 接口"""
    return await lawfirm_service.get_firms(db, page, page_size, keyword)


# 兼容前端路由：/lawfirm/{firmId}/lawyers（对应 /lawfirm/lawyers）
@router.get("/{firm_id}/lawyers", response_model=LawyerListResponse,
            summary="获取律所律师列表（兼容路由）")
async def get_lawyers_by_firm_compat(
    firm_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """获取指定律所的律师列表，兼容前端 /lawfirm/{firmId}/lawyers 接口"""
    return await lawyer_service.get_lawyers(db, page, page_size, firm_id=firm_id)


# 兼容前端路由：/lawfirm/{firmId}/bookings（对应 /lawfirm/consultations）
@router.post("/{firm_id}/bookings", summary="预约咨询（兼容路由）")
async def book_consultation_compat(
    firm_id: int,
    data: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """预约咨询，兼容前端 /lawfirm/{firmId}/bookings 接口"""
    lawyer_id = data.get("lawyer_id")
    time = data.get("time")
    note = data.get("note")
    
    if not lawyer_id or not time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必要参数：lawyer_id 和 time"
        )
    
    consultation = await lawyer_service.create_consultation(
        db, firm_id, int(current_user.id), lawyer_id, time, note
    )
    return {"message": "预约成功", "consultation_id": consultation.id}


__all__ = ["router"]
