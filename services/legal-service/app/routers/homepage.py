"""律师主页路由"""
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.lawyer_profile import LawyerHomepage

router = APIRouter()


@router.get("/lawyers/{lawyer_id}/homepage")
async def get_lawyer_homepage(lawyer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
    )
    homepage = result.scalar_one_or_none()
    if not homepage:
        return {"lawyer_id": lawyer_id, "is_published": False}
    return homepage


@router.post("/lawyers/{lawyer_id}/homepage")
async def create_lawyer_homepage(lawyer_id: int, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="律师主页已存在，请使用 PUT 更新")
    homepage = LawyerHomepage(lawyer_id=lawyer_id)
    db.add(homepage)
    await db.commit()
    await db.refresh(homepage)
    return homepage


@router.put("/lawyers/{lawyer_id}/homepage")
async def update_lawyer_homepage(lawyer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
    )
    homepage = result.scalar_one_or_none()
    if not homepage:
        homepage = LawyerHomepage(lawyer_id=lawyer_id)
        db.add(homepage)
    await db.commit()
    await db.refresh(homepage)
    return homepage


@router.post("/lawyers/{lawyer_id}/homepage/publish")
async def publish_lawyer_homepage(lawyer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
    )
    homepage = result.scalar_one_or_none()
    if not homepage:
        raise HTTPException(status_code=404, detail="律师主页不存在")
    homepage.is_published = True
    await db.commit()
    return {"message": "发布成功", "is_published": True}


class CaseStudyRequest(BaseModel):
    title: str
    description: str
    result: str
    category: Optional[str] = None


@router.post("/lawyers/{lawyer_id}/homepage/case-studies")
async def add_case_study(
    lawyer_id: int,
    body: CaseStudyRequest,
    db: AsyncSession = Depends(get_db),
):
    """添加成功案例"""
    result = await db.execute(
        select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
    )
    homepage = result.scalar_one_or_none()
    if not homepage:
        homepage = LawyerHomepage(lawyer_id=lawyer_id)
        db.add(homepage)

    case_studies = json.loads(homepage.case_studies) if homepage.case_studies else []
    case_study = {
        "id": len(case_studies) + 1,
        "title": body.title,
        "description": body.description,
        "result": body.result,
        "category": body.category,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    case_studies.append(case_study)
    homepage.case_studies = json.dumps(case_studies, ensure_ascii=False)
    await db.commit()

    return {"case_study": case_study, "total": len(case_studies)}


@router.get("/lawyers/{lawyer_id}/homepage/case-studies")
async def get_case_studies(
    lawyer_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取成功案例列表"""
    result = await db.execute(
        select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
    )
    homepage = result.scalar_one_or_none()
    case_studies = json.loads(homepage.case_studies) if homepage and homepage.case_studies else []
    return {"lawyer_id": lawyer_id, "case_studies": case_studies, "total": len(case_studies)}


@router.delete("/lawyers/{lawyer_id}/homepage/case-studies/{case_id}")
async def delete_case_study(
    lawyer_id: int,
    case_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除成功案例"""
    result = await db.execute(
        select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
    )
    homepage = result.scalar_one_or_none()
    if not homepage or not homepage.case_studies:
        raise HTTPException(status_code=404, detail="案例不存在")

    case_studies = json.loads(homepage.case_studies)
    case_studies = [c for c in case_studies if c.get("id") != case_id]
    homepage.case_studies = json.dumps(case_studies, ensure_ascii=False)
    await db.commit()

    return {"deleted": True, "case_id": case_id, "total": len(case_studies)}


@router.get("/lawyers/{lawyer_id}/homepage/public")
async def get_public_homepage(
    lawyer_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取律师公开主页（含 SEO 信息）"""
    result = await db.execute(
        select(LawyerHomepage).where(
            LawyerHomepage.lawyer_id == lawyer_id,
            LawyerHomepage.is_published == True,
        )
    )
    homepage = result.scalar_one_or_none()

    if not homepage:
        return {"lawyer_id": lawyer_id, "is_published": False}

    homepage.view_count = (homepage.view_count or 0) + 1
    await db.commit()

    seo = {
        "title": homepage.seo_title or f"律师 {lawyer_id} - 法律服务平台",
        "description": homepage.seo_description or homepage.bio[:160] if homepage.bio else "",
        "keywords": homepage.seo_keywords or "",
    }

    case_studies = json.loads(homepage.case_studies) if homepage.case_studies else []

    return {
        "lawyer_id": lawyer_id,
        "is_published": True,
        "banner_image": homepage.banner_image,
        "profile_image": homepage.profile_image,
        "slogan": homepage.slogan,
        "bio": homepage.bio,
        "specialties_display": homepage.specialties_display,
        "achievements": homepage.achievements,
        "education": homepage.education,
        "service_areas": homepage.service_areas,
        "service_hours": homepage.service_hours,
        "response_time": homepage.response_time,
        "case_studies": case_studies,
        "video_url": homepage.video_url,
        "video_cover": homepage.video_cover,
        "view_count": homepage.view_count,
        "seo": seo,
        "theme_color": homepage.theme_color,
        "background_color": homepage.background_color,
    }


@router.get("/lawyers/{lawyer_id}/homepage/qrcode")
async def get_qrcode_url(
    lawyer_id: int,
    path: Optional[str] = Query(None, description="小程序页面路径"),
    db: AsyncSession = Depends(get_db),
):
    """生成律师主页小程序码链接"""
    qr_path = path or f"pages/lawyer/detail?id={lawyer_id}"
    token = hashlib.md5(f"lawyer_{lawyer_id}_qrcode".encode()).hexdigest()[:8]

    qrcode_url = f"https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket={token}"

    return {
        "lawyer_id": lawyer_id,
        "qrcode_url": qrcode_url,
        "path": qr_path,
    }


@router.patch("/lawyers/{lawyer_id}/homepage")
async def partial_update_homepage(
    lawyer_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """部分更新律师主页信息"""
    result = await db.execute(
        select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
    )
    homepage = result.scalar_one_or_none()
    if not homepage:
        homepage = LawyerHomepage(lawyer_id=lawyer_id)
        db.add(homepage)

    updatable_fields = [
        "banner_image", "profile_image", "slogan", "bio",
        "specialties_display", "achievements", "education",
        "service_areas", "service_hours", "response_time",
        "contact_phone", "contact_email", "wechat_qrcode",
        "weibo_url", "linkedin_url", "zhihu_url",
        "video_url", "video_cover",
        "seo_title", "seo_description", "seo_keywords",
        "theme_color", "background_color",
    ]

    for field in updatable_fields:
        if field in body:
            setattr(homepage, field, body[field])

    homepage.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(homepage)

    return homepage