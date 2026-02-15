"""律师管理路由"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...schemas.lawfirm import LawyerCreate, LawyerResponse, LawyerListResponse, LawyerRankingResponse
from ...services.lawfirm_service import lawyer_service
from ...utils.deps import require_admin

router = APIRouter(prefix="/lawyers", tags=["律师管理"])


@router.get("", response_model=LawyerListResponse, summary="获取律师列表")
async def get_lawyers(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    firm_id: int | None = None,
    specialty: str | None = None,
    keyword: str | None = None,
):
    """获取律师列表 - 使用selectinload预加载律所信息避免N+1"""
    # lawyer_service.get_list 已使用 selectinload(Lawyer.firm) 预加载律所信息
    lawyers, total = await lawyer_service.get_list(db, page, page_size, firm_id, specialty, keyword)

    items = []
    for lawyer in lawyers:
        # 由于使用了selectinload，访问lawyer.firm.name不会触发额外查询
        items.append(LawyerResponse(
            id=lawyer.id,
            user_id=lawyer.user_id,
            firm_id=lawyer.firm_id,
            name=lawyer.name,
            avatar=lawyer.avatar,
            title=lawyer.title,
            license_no=lawyer.license_no,
            phone=lawyer.phone,
            email=lawyer.email,
            introduction=lawyer.introduction,
            specialties=lawyer.specialties,
            experience_years=lawyer.experience_years,
            case_count=lawyer.case_count,
            rating=lawyer.rating,
            review_count=lawyer.review_count,
            consultation_fee=lawyer.consultation_fee,
            is_verified=lawyer.is_verified,
            is_active=lawyer.is_active,
            created_at=lawyer.created_at,
            firm_name=lawyer.firm.name if lawyer.firm else None
        ))

    return LawyerListResponse(items=items, total=total,
                              page=page, page_size=page_size)


@router.get("/{lawyer_id}", response_model=LawyerResponse, summary="获取律师详情")
async def get_lawyer(
        lawyer_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    """获取律师详情"""
    lawyer = await lawyer_service.get_by_id(db, lawyer_id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    return LawyerResponse(
        id=lawyer.id,
        user_id=lawyer.user_id,
        firm_id=lawyer.firm_id,
        name=lawyer.name,
        avatar=lawyer.avatar,
        title=lawyer.title,
        license_no=lawyer.license_no,
        phone=lawyer.phone,
        email=lawyer.email,
        introduction=lawyer.introduction,
        specialties=lawyer.specialties,
        experience_years=lawyer.experience_years,
        case_count=lawyer.case_count,
        rating=lawyer.rating,
        review_count=lawyer.review_count,
        consultation_fee=lawyer.consultation_fee,
        is_verified=lawyer.is_verified,
        is_active=lawyer.is_active,
        created_at=lawyer.created_at,
        firm_name=lawyer.firm.name if lawyer.firm else None
    )


@router.post("", response_model=LawyerResponse, summary="创建律师")
async def create_lawyer(
    data: LawyerCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """创建律师（需要管理员权限）"""
    _ = current_user
    lawyer = await lawyer_service.create(db, data)
    return LawyerResponse(
        id=lawyer.id,
        user_id=lawyer.user_id,
        firm_id=lawyer.firm_id,
        name=lawyer.name,
        avatar=lawyer.avatar,
        title=lawyer.title,
        license_no=lawyer.license_no,
        phone=lawyer.phone,
        email=lawyer.email,
        introduction=lawyer.introduction,
        specialties=lawyer.specialties,
        experience_years=lawyer.experience_years,
        case_count=lawyer.case_count,
        rating=lawyer.rating,
        review_count=lawyer.review_count,
        consultation_fee=lawyer.consultation_fee,
        is_verified=lawyer.is_verified,
        is_active=lawyer.is_active,
        created_at=lawyer.created_at,
        firm_name=None
    )


@router.get("/ranking", response_model=LawyerRankingResponse, summary="律师排行榜")
async def get_lawyer_ranking(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    period: str | None = None,
):
    """获取律师排行榜"""
    lawyers = await lawyer_service.get_ranking(db, limit, period)
    return {"lawyers": lawyers}
