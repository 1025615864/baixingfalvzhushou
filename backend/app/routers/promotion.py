"""SEO 与裂变推广 API 路由

提供邀请链接生成、分享追踪、SEO 基础配置等功能。
"""
from __future__ import annotations

import uuid
import secrets
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..services.referral_service import referral_service
from ..utils.deps import get_current_user_optional, get_current_user

router = APIRouter(prefix="/promotion", tags=["SEO与裂变"])

# SEO 配置
SEO_CONFIG = {
    "title_template": "{title} - 百姓助手法律服务平台",
    "description": "专业法律咨询服务，提供婚姻、劳动、房产等领域的法律咨询和文书服务。",
    "keywords": "法律咨询,法律服务,律师咨询,婚姻法律,劳动法律,文书服务",
    "sitemap": {
        "changefreq": "daily",
        "priority": {
            "home": 1.0,
            "news": 0.8,
            "consultation": 0.6,
            "document": 0.7},
    },
}


@router.get("/seo/config")
async def get_seo_config() -> dict:
    """获取 SEO 配置信息"""
    return {
        "config": SEO_CONFIG,
        "structured_data": {
            "@context": "https://schema.org",
            "@type": "LegalService",
            "name": "百姓助手法律服务平台",
            "description": SEO_CONFIG["description"],
            "url": "https://baixing.com",
        },
    }


@router.get("/seo/sitemap-index")
async def get_sitemap_index() -> dict:
    """获取站点地图索引"""
    return {
        "sitemaps": [
            {"loc": "/api/promotion/seo/sitemap-news.xml", "lastmod": "2026-01-24"},
            {"loc": "/api/promotion/seo/sitemap-docs.xml", "lastmod": "2026-01-24"},
            {"loc": "/api/promotion/seo/sitemap-categories.xml",
                "lastmod": "2026-01-24"},
        ]
    }


@router.get("/invite/generate")
async def generate_invite_code(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """生成用户邀请码和邀请链接"""
    invite_code = await referral_service.generate_invite_code(db, current_user.id)

    return {
        "invite_code": invite_code,
        "invite_url": f"https://baixing.com/register?ref={invite_code}",
        "short_url": f"https://bxz.cn/{invite_code}",
        "qrcode_url": f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://baixing.com/register?ref={invite_code}",
    }


@router.get("/invite/stats")
async def get_invite_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """获取邀请统计"""
    stats = await referral_service.get_invite_stats(db, current_user.id)
    return stats


@router.get("/invite/history")
async def get_invite_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(ge=1, default=1),
    page_size: int = Query(ge=1, le=100, default=20),
) -> dict:
    """获取邀请历史记录"""
    history = await referral_service.get_invite_history(db, current_user.id, page, page_size)
    return history


@router.post("/invite/claim")
async def claim_invite_reward(
    invite_code: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """领取邀请奖励"""
    result = await referral_service.claim_reward(db, current_user.id, invite_code)
    return result


@router.get("/share/news/{news_id}")
async def get_news_share_link(
    news_id: int,
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> dict:
    """获取新闻分享链接"""
    share_token = secrets.token_urlsafe(16)

    return {
        "share_url": f"https://baixing.com/news/{news_id}?share={share_token}",
        "short_url": f"https://bxz.cn/n/{news_id}",
        "qrcode_url": f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://baixing.com/news/{news_id}",
        "expires_in": 86400,  # 24小时
    }


@router.get("/share/document/{doc_id}")
async def get_document_share_link(
    doc_id: int,
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> dict:
    """获取文书分享链接"""
    share_token = secrets.token_urlsafe(16)

    return {
        "share_url": f"https://baixing.com/document/{doc_id}?share={share_token}",
        "short_url": f"https://bxz.cn/d/{doc_id}",
        "qrcode_url": f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://baixing.com/document/{doc_id}",
        "expires_in": 86400,
    }


@router.get("/analytics/invitation")
async def get_invitation_analytics(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """获取邀请转化分析"""
    return await referral_service.get_analytics(db, current_user.id)


@router.get("/ranking/invite")
async def get_invite_ranking(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(ge=1, le=100, default=10),
) -> dict:
    """获取邀请排行榜"""
    return await referral_service.get_ranking(db, limit)
