"""运营配置管理路由"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.ops.config_service import ConfigService
from app.middleware.ops_auth import require_ops_role

try:
    from services.common.middleware.admin_auth import require_domain_role
except ImportError:
    from fastapi import Depends, HTTPException
    def require_domain_role(domain: str, roles=None):
        async def _checker(request=None):
            from fastapi import Request
            if request and hasattr(request, 'headers'):
                role = request.headers.get("X-Admin-Role", "")
                if role in {"super_admin", "admin"}:
                    return None
                if roles and role not in roles:
                    raise HTTPException(status_code=403, detail=f"需要角色: {', '.join(roles)}")
            return None
        return _checker

router = APIRouter(prefix="/api/v1/community/ops/config", tags=["运营配置"], dependencies=[Depends(require_domain_role("community", roles=["community_admin"]))])


class RulesUpdateRequest(BaseModel):
    post_min_length: Optional[int] = None
    post_max_length: Optional[int] = None
    comment_max_length: Optional[int] = None
    posts_per_day_limit: Optional[int] = None
    comments_per_hour_limit: Optional[int] = None
    new_user_post_delay_hours: Optional[int] = None
    auto_close_days: Optional[int] = None
    require_approval_for_new_users: Optional[bool] = None
    allow_anonymous_view: Optional[bool] = None
    lawyer_badge_enabled: Optional[bool] = None


class SensitiveWordsRequest(BaseModel):
    words: List[str]
    category: str = "general"


class AutoModerationRequest(BaseModel):
    ai_review_enabled: Optional[bool] = None
    ai_confidence_threshold: Optional[float] = None
    auto_reject_threshold: Optional[float] = None
    new_user_always_review: Optional[bool] = None
    reported_threshold: Optional[int] = None
    link_in_post_trigger_review: Optional[bool] = None


@router.get("/rules")
async def get_rules(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("community_director"))
):
    service = ConfigService(db)
    rules = await service.get_community_rules()
    return {"success": True, "data": rules}


@router.put("/rules")
async def update_rules(
    req: RulesUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("community_director"))
):
    service = ConfigService(db)
    current_rules = await service.get_community_rules()

    update_data = req.model_dump(exclude_unset=True)
    current_rules.update(update_data)

    await service.update_community_rules(current_rules, current_user["id"])
    return {"success": True, "message": "社区规则已更新"}


@router.get("/sensitive-words")
async def get_sensitive_words(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("content_mod", "community_director"))
):
    service = ConfigService(db)
    words = await service.get_sensitive_words(category)
    return {"success": True, "data": words}


@router.post("/sensitive-words")
async def add_sensitive_words(
    req: SensitiveWordsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("content_mod", "community_director"))
):
    service = ConfigService(db)
    added = await service.add_sensitive_words(req.words, req.category)
    return {"success": True, "message": f"已添加{added}个敏感词"}


@router.delete("/sensitive-words")
async def remove_sensitive_words(
    words: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("content_mod", "community_director"))
):
    service = ConfigService(db)
    removed = await service.remove_sensitive_words(words)
    return {"success": True, "message": f"已删除{removed}个敏感词"}


@router.get("/auto-moderation")
async def get_auto_moderation(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("content_mod", "community_director"))
):
    service = ConfigService(db)
    config = await service.get_auto_moderation_config()
    return {"success": True, "data": config}


@router.put("/auto-moderation")
async def update_auto_moderation(
    req: AutoModerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("content_mod", "community_director"))
):
    service = ConfigService(db)
    current_config = await service.get_auto_moderation_config()

    update_data = req.model_dump(exclude_unset=True)
    current_config.update(update_data)

    await service.update_auto_moderation_config(current_config, current_user["id"])
    return {"success": True, "message": "自动审核配置已更新"}
