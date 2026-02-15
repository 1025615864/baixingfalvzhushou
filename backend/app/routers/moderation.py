"""内容审核 API 路由

提供关键词过滤、AI初筛、敏感内容自动标记等功能。
"""
from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..services.content_moderation import KeywordFilter, ContentModerationService
from ..utils.deps import get_current_user_optional, get_current_user, require_admin
from ..middleware.rate_limit import keyword_check_limiter

router = APIRouter(prefix="/moderation", tags=["内容审核"])

# 服务实例
keyword_filter = KeywordFilter()
moderation_service = ContentModerationService()


@router.post("/keyword/check")
async def check_keyword(
        content: str, categories: list[str] | None = None) -> dict:
    """关键词检查（带限流保护）

    Args:
        content: 待检查内容
        categories: 分类列表

    Returns:
        检查结果
    """
    # 限流检查（使用客户端IP作为key）
    client_ip = "anonymous"
    if not keyword_check_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    result = keyword_filter.check_content(content, categories)
    return result


@router.post("/keyword/add")
async def add_keyword(
    _current_user: Annotated[User, Depends(require_admin)],
    keyword: str,
    category: str = "custom",
    severity: str = "medium",
) -> dict:
    """添加关键词（需要管理员权限）"""
    result = keyword_filter.add_keyword(keyword, category, severity)
    return result


@router.get("/keyword/list")
async def list_keywords(
    _current_user: Annotated[User, Depends(require_admin)],
    category: str | None = None,
) -> dict:
    """获取关键词列表（仅管理员可访问）"""
    if category:
        keywords = [
            k for k in keyword_filter._keywords.values()
            if k["category"] == category
        ]
    else:
        keywords = list(keyword_filter._keywords.values())

    return {
        "keywords": keywords,
        "total": len(keywords),
        "categories": list(keyword_filter._categories.keys()),
    }


@router.post("/check")
async def check_content(
    content: str,
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> dict:
    """综合内容审核

    集成关键词过滤，返回综合审核结果

    Args:
        content: 待检查内容

    Returns:
        综合审核结果
    """
    # 关键词检查
    keyword_result = keyword_filter.check_content(content)
    risk_score = keyword_result["risk_score"]

    # 判定结果
    if risk_score >= 70:
        status = "blocked"
        message = "内容包含敏感信息，已被拦截"
    elif risk_score >= 30:
        status = "warning"
        message = "内容可能包含敏感信息，请注意"
    else:
        status = "passed"
        message = "内容审核通过"

    return {
        "status": status,
        "message": message,
        "risk_score": risk_score,
        "keyword_result": keyword_result,
        "suggested_action": "approve" if status == "passed" else (
            "reject" if status == "blocked" else "review"),
    }


@router.get("/stats")
async def get_moderation_stats() -> dict:
    """获取审核统计"""
    return {
        "total_checks": moderation_service.get_total_checks(),
        "blocked_count": moderation_service.get_blocked_count(),
        "warning_count": moderation_service.get_warning_count(),
        "passed_count": moderation_service.get_passed_count(),
        "block_rate": moderation_service.get_block_rate(),
        "categories": {
            "political": moderation_service.get_category_count("political"),
            "pornographic": moderation_service.get_category_count("pornographic"),
            "violence": moderation_service.get_category_count("violence"),
            "advertisement": moderation_service.get_category_count("advertisement"),
        },
    }
