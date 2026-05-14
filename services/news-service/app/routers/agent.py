"""新闻运营助手 Agent 路由 - AI辅助写作/审核/运营建议"""
from typing import List, Optional

import logging

from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.news_agent_service import news_agent_service
from app.services.news_admin_service import news_admin_service
from app.database import get_db, AsyncSession
from app.models import News

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi import status as http_status
    import os

    security = HTTPBearer(auto_error=False)

    class AdminUser:
        def __init__(self, user_id: int = 0, role: str = "admin", permissions: Optional[list] = None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in {"super_admin", "admin"}

    async def get_admin_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> AdminUser:
        if not credentials:
            raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="未提供认证凭据")
        if os.getenv("DISABLE_AUTH", "").lower() in {"1", "true", "yes"}:
            return AdminUser(user_id=1, role="super_admin")
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="认证服务不可用")

    def require_domain_role(domain: str, roles: Optional[List[str]] = None):
        async def domain_checker(admin: AdminUser = Depends(get_admin_user)):
            if admin.is_super_admin:
                return admin
            if roles and admin.role not in roles:
                raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=f"需要角色: {', '.join(roles)}，当前角色: {admin.role}")
            return admin
        return domain_checker

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(require_domain_role("news"))])


class GenerateTitleRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=10000)
    original_title: Optional[str] = None


class GenerateSummaryRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=20000)
    title: Optional[str] = None


class RecommendCategoryRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=10000)
    title: Optional[str] = None


class RecommendTagsRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=10000)
    title: Optional[str] = None


class ReviewContentRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=20000)
    title: Optional[str] = None


class AssistWritingRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500)
    key_points: Optional[List[str]] = None
    style: Optional[str] = None
    reference_content: Optional[str] = None


class NewsIdRequest(BaseModel):
    news_id: int = Field(..., ge=1)


@router.post("/generate-title")
async def generate_titles(body: GenerateTitleRequest):
    """AI生成新闻标题建议"""
    try:
        result = await news_agent_service.generate_titles(body.content, body.original_title)
        return result
    except Exception as e:
        logger.error(f"AI title generation failed: {e}")
        raise HTTPException(status_code=500, detail="AI标题生成失败，请稍后重试")


@router.post("/generate-summary")
async def generate_summary(body: GenerateSummaryRequest):
    """AI生成新闻摘要"""
    try:
        result = await news_agent_service.generate_summary(body.content, body.title)
        return result
    except Exception as e:
        logger.error(f"AI summary generation failed: {e}")
        raise HTTPException(status_code=500, detail="AI摘要生成失败，请稍后重试")


@router.post("/recommend-category")
async def recommend_category(body: RecommendCategoryRequest):
    """AI推荐新闻分类"""
    try:
        result = await news_agent_service.recommend_category(body.content, body.title)
        return result
    except Exception as e:
        logger.error(f"AI category recommendation failed: {e}")
        raise HTTPException(status_code=500, detail="AI分类推荐失败，请稍后重试")


@router.post("/recommend-tags")
async def recommend_tags(body: RecommendTagsRequest):
    """AI推荐新闻标签"""
    try:
        result = await news_agent_service.recommend_tags(body.content, body.title)
        return result
    except Exception as e:
        logger.error(f"AI tag recommendation failed: {e}")
        raise HTTPException(status_code=500, detail="AI标签推荐失败，请稍后重试")


@router.post("/review-content")
async def review_content(body: ReviewContentRequest):
    """AI审核新闻内容质量"""
    try:
        result = await news_agent_service.review_content(body.content, body.title)
        return result
    except Exception as e:
        logger.error(f"AI content review failed: {e}")
        raise HTTPException(status_code=500, detail="AI内容审核失败，请稍后重试")


@router.post("/assist-writing")
async def assist_writing(body: AssistWritingRequest):
    """AI辅助撰写新闻稿件"""
    try:
        result = await news_agent_service.assist_writing(
            topic=body.topic,
            key_points=body.key_points,
            style=body.style,
            reference_content=body.reference_content,
        )
        return result
    except Exception as e:
        logger.error(f"AI writing assist failed: {e}")
        raise HTTPException(status_code=500, detail="AI写作辅助失败，请稍后重试")


@router.post("/operations-suggestions")
async def operations_suggestions(db: AsyncSession = Depends(get_db)):
    """AI运营策略建议（基于当前运营数据）"""
    try:
        stats = await news_admin_service.get_dashboard_stats(db)
        result = await news_agent_service.operations_suggestions(stats)
        return result
    except Exception as e:
        logger.error(f"AI operations suggestions failed: {e}")
        raise HTTPException(status_code=500, detail="AI运营建议生成失败，请稍后重试")


@router.post("/news/{news_id}/smart-enhance")
async def smart_enhance_news(
    news_id: int,
    db: AsyncSession = Depends(get_db),
):
    """AI一键增强新闻（标题+摘要+分类+标签+内容审核）"""
    from sqlalchemy import select
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")

    enhance_result = {}
    errors = []

    try:
        titles = await news_agent_service.generate_titles(news.content, news.title)
        enhance_result["titles"] = titles
    except Exception as e:
        errors.append(f"标题生成失败: {str(e)}")

    try:
        summary = await news_agent_service.generate_summary(news.content, news.title)
        enhance_result["summary"] = summary
    except Exception as e:
        errors.append(f"摘要生成失败: {str(e)}")

    try:
        category = await news_agent_service.recommend_category(news.content, news.title)
        enhance_result["category"] = category
    except Exception as e:
        errors.append(f"分类推荐失败: {str(e)}")

    try:
        tags = await news_agent_service.recommend_tags(news.content, news.title)
        enhance_result["tags"] = tags
    except Exception as e:
        errors.append(f"标签推荐失败: {str(e)}")

    try:
        review = await news_agent_service.review_content(news.content, news.title)
        enhance_result["review"] = review
    except Exception as e:
        errors.append(f"内容审核失败: {str(e)}")

    enhance_result["errors"] = errors if errors else None
    return enhance_result
