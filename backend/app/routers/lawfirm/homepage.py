"""律师主页定制路由"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...schemas.lawfirm import (
    LawyerHomepageCreate, LawyerHomepageUpdate,
    LawyerHomepageResponse, LawyerHomepagePublicResponse,
)
from ...services.lawyer_homepage_service import LawyerHomepageService
from ...utils.deps import get_current_user

router = APIRouter(prefix="/lawyer/homepage", tags=["律师主页"])


def _serialize_homepage(homepage) -> LawyerHomepageResponse:
    return LawyerHomepageResponse(
        id=homepage.id,
        lawyer_id=homepage.lawyer_id,
        banner_image=homepage.banner_image,
        profile_image=homepage.profile_image,
        slogan=homepage.slogan,
        bio=homepage.bio,
        specialties_display=homepage.specialties_display,
        achievements=homepage.achievements,
        education=homepage.education,
        service_areas=homepage.service_areas,
        service_hours=homepage.service_hours,
        response_time=homepage.response_time,
        contact_phone=homepage.contact_phone,
        contact_email=homepage.contact_email,
        wechat_qrcode=homepage.wechat_qrcode,
        weibo_url=homepage.weibo_url,
        linkedin_url=homepage.linkedin_url,
        zhihu_url=homepage.zhihu_url,
        case_studies=homepage.case_studies,
        video_url=homepage.video_url,
        video_cover=homepage.video_cover,
        seo_title=homepage.seo_title,
        seo_description=homepage.seo_description,
        seo_keywords=homepage.seo_keywords,
        theme_color=homepage.theme_color,
        background_color=homepage.background_color,
        is_published=homepage.is_published,
        view_count=homepage.view_count,
        created_at=homepage.created_at,
        updated_at=homepage.updated_at,
    )


async def _require_verified_lawyer(db: AsyncSession, current_user: User):
    """获取当前用户的律师信息"""
    from ...models.lawfirm import Lawyer
    from sqlalchemy import select

    res = await db.execute(
        select(Lawyer).where(
            Lawyer.user_id == int(current_user.id),
            Lawyer.is_active,
        )
    )
    lawyer = res.scalar_one_or_none()
    if not lawyer:
        raise HTTPException(status_code=403, detail="未绑定律师资料")
    return lawyer


@router.get("", response_model=LawyerHomepageResponse, summary="律师-获取我的主页")
async def lawyer_get_my_homepage(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师获取自己的主页"""
    lawyer = await _require_verified_lawyer(db, current_user)

    homepage = await LawyerHomepageService.get_by_lawyer_id(db, int(lawyer.id))
    if not homepage:
        raise HTTPException(status_code=404, detail="主页不存在，请先创建")

    return _serialize_homepage(homepage)


@router.post("", response_model=LawyerHomepageResponse, summary="律师-创建主页")
async def lawyer_create_homepage(
    data: LawyerHomepageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师创建主页"""
    lawyer = await _require_verified_lawyer(db, current_user)

    homepage = await LawyerHomepageService.create(db, int(lawyer.id), data)

    return LawyerHomepageResponse(
        id=homepage.id,
        lawyer_id=homepage.lawyer_id,
        banner_image=homepage.banner_image,
        profile_image=homepage.profile_image,
        slogan=homepage.slogan,
        bio=homepage.bio,
        specialties_display=homepage.specialties_display,
        achievements=homepage.achievements,
        education=homepage.education,
        service_areas=homepage.service_areas,
        service_hours=homepage.service_hours,
        response_time=homepage.response_time,
        contact_phone=homepage.contact_phone,
        contact_email=homepage.contact_email,
        wechat_qrcode=homepage.wechat_qrcode,
        weibo_url=homepage.weibo_url,
        linkedin_url=homepage.linkedin_url,
        zhihu_url=homepage.zhihu_url,
        case_studies=homepage.case_studies,
        video_url=homepage.video_url,
        video_cover=homepage.video_cover,
        seo_title=homepage.seo_title,
        seo_description=homepage.seo_description,
        seo_keywords=homepage.seo_keywords,
        theme_color=homepage.theme_color,
        background_color=homepage.background_color,
        is_published=homepage.is_published,
        view_count=homepage.view_count,
        created_at=homepage.created_at,
        updated_at=homepage.updated_at,
    )


@router.put("", response_model=LawyerHomepageResponse, summary="律师-更新主页")
async def lawyer_update_homepage(
    data: LawyerHomepageUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师更新主页"""
    lawyer = await _require_verified_lawyer(db, current_user)

    homepage = await LawyerHomepageService.update(db, int(lawyer.id), data)

    if not homepage:
        raise HTTPException(status_code=404, detail="主页不存在")

    return LawyerHomepageResponse(
        id=homepage.id,
        lawyer_id=homepage.lawyer_id,
        banner_image=homepage.banner_image,
        profile_image=homepage.profile_image,
        slogan=homepage.slogan,
        bio=homepage.bio,
        specialties_display=homepage.specialties_display,
        achievements=homepage.achievements,
        education=homepage.education,
        service_areas=homepage.service_areas,
        service_hours=homepage.service_hours,
        response_time=homepage.response_time,
        contact_phone=homepage.contact_phone,
        contact_email=homepage.contact_email,
        wechat_qrcode=homepage.wechat_qrcode,
        weibo_url=homepage.weibo_url,
        linkedin_url=homepage.linkedin_url,
        zhihu_url=homepage.zhihu_url,
        case_studies=homepage.case_studies,
        video_url=homepage.video_url,
        video_cover=homepage.video_cover,
        seo_title=homepage.seo_title,
        seo_description=homepage.seo_description,
        seo_keywords=homepage.seo_keywords,
        theme_color=homepage.theme_color,
        background_color=homepage.background_color,
        is_published=homepage.is_published,
        view_count=homepage.view_count,
        created_at=homepage.created_at,
        updated_at=homepage.updated_at,
    )


@router.post("/publish", response_model=LawyerHomepageResponse,
             summary="律师-发布主页")
async def lawyer_publish_homepage(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师发布主页"""
    lawyer = await _require_verified_lawyer(db, current_user)

    homepage = await LawyerHomepageService.publish(db, int(lawyer.id))

    if not homepage:
        raise HTTPException(status_code=404, detail="主页不存在")

    return _serialize_homepage(homepage)


@router.post("/unpublish", response_model=LawyerHomepageResponse,
             summary="律师-取消发布主页")
async def lawyer_unpublish_homepage(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师取消发布主页"""
    lawyer = await _require_verified_lawyer(db, current_user)

    homepage = await LawyerHomepageService.unpublish(db, int(lawyer.id))

    if not homepage:
        raise HTTPException(status_code=404, detail="主页不存在")

    return _serialize_homepage(homepage)


@router.get("/lawyers/{lawyer_id}",
            response_model=LawyerHomepagePublicResponse, summary="获取律师公开主页")
async def get_lawyer_public_homepage(
    lawyer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取律师的公开主页"""
    homepage = await LawyerHomepageService.get_public_homepage(db, lawyer_id)

    if not homepage:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="主页不存在")

    return homepage
