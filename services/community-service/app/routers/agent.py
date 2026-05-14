"""社区运营助手 Agent 路由 - AI辅助内容审核/热点发现/用户画像/摘要生成"""
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from app.services.community_agent_service import community_agent_service
from app.database import get_db, AsyncSession
from app.models import Post

logger = logging.getLogger(__name__)

router = APIRouter()

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    import os
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi import status as http_status

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
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="未提供认证凭据",
            )
        if os.getenv("DISABLE_AUTH", "").lower() in {"1", "true", "yes"}:
            return AdminUser(user_id=1, role="super_admin")
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="认证服务不可用",
        )

    def require_domain_role(domain: str, roles: Optional[List[str]] = None):
        async def domain_checker(admin: AdminUser = Depends(get_admin_user)):
            if admin.is_super_admin:
                return admin
            if roles and admin.role not in roles:
                raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=f"需要角色: {', '.join(roles)}")
            return admin
        return domain_checker


router = APIRouter(dependencies=[Depends(require_domain_role("community"))])


class ModerateContentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=20000)
    title: Optional[str] = None


class DiscoverTrendingRequest(BaseModel):
    posts_data: List[Dict[str, Any]] = Field(..., min_length=1)


class AnalyzeUserProfileRequest(BaseModel):
    user_data: Dict[str, Any]


class GenerateSummaryRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=20000)
    title: Optional[str] = None


class SuggestModerationRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=20000)
    violation_type: str = Field(..., min_length=1, max_length=100)


@router.post("/moderate-content")
async def moderate_content(
    body: ModerateContentRequest,
    admin: AdminUser = Depends(get_admin_user),
):
    """智能内容审核：自动检测违规内容"""
    try:
        result = await community_agent_service.moderate_content(body.content, body.title)
        return result
    except Exception as e:
        logger.error(f"AI content moderation failed: {e}")
        raise HTTPException(status_code=500, detail="AI内容审核失败，请稍后重试")


@router.post("/discover-trending")
async def discover_trending(
    body: DiscoverTrendingRequest,
    admin: AdminUser = Depends(get_admin_user),
):
    """热点发现：基于互动数据自动识别热点话题"""
    try:
        result = await community_agent_service.discover_trending(body.posts_data)
        return result
    except Exception as e:
        logger.error(f"AI trending discovery failed: {e}")
        raise HTTPException(status_code=500, detail="AI热点发现失败，请稍后重试")


@router.post("/analyze-user-profile")
async def analyze_user_profile(
    body: AnalyzeUserProfileRequest,
    admin: AdminUser = Depends(get_admin_user),
):
    """用户画像分析：行为分析 + 标签推荐"""
    try:
        result = await community_agent_service.analyze_user_profile(body.user_data)
        return result
    except Exception as e:
        logger.error(f"AI user profile analysis failed: {e}")
        raise HTTPException(status_code=500, detail="AI用户画像分析失败，请稍后重试")


@router.post("/generate-summary")
async def generate_summary(
    body: GenerateSummaryRequest,
    admin: AdminUser = Depends(get_admin_user),
):
    """帖子摘要生成：为长帖生成摘要"""
    try:
        result = await community_agent_service.generate_summary(body.content, body.title)
        return result
    except Exception as e:
        logger.error(f"AI summary generation failed: {e}")
        raise HTTPException(status_code=500, detail="AI摘要生成失败，请稍后重试")


@router.post("/suggest-moderation")
async def suggest_moderation(
    body: SuggestModerationRequest,
    admin: AdminUser = Depends(get_admin_user),
):
    """建议审核操作：根据违规类型建议处理方式"""
    try:
        result = await community_agent_service.suggest_moderation_action(body.content, body.violation_type)
        return result
    except Exception as e:
        logger.error(f"AI moderation suggestion failed: {e}")
        raise HTTPException(status_code=500, detail="AI审核建议生成失败，请稍后重试")


@router.post("/posts/{post_id}/smart-moderate")
async def smart_moderate_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """一键智能审核：综合审核+摘要+建议"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    smart_result = {}
    errors = []

    try:
        moderation = await community_agent_service.moderate_content(post.content, post.title)
        smart_result["moderation"] = moderation
    except Exception as e:
        errors.append(f"内容审核失败: {str(e)}")

    try:
        summary = await community_agent_service.generate_summary(post.content, post.title)
        smart_result["summary"] = summary
    except Exception as e:
        errors.append(f"摘要生成失败: {str(e)}")

    import json
    try:
        moderation_data = smart_result.get("moderation", {})
        moderation_text = moderation_data.get("moderation", "{}") if isinstance(moderation_data, dict) else "{}"
        parsed = json.loads(moderation_text) if isinstance(moderation_text, str) else moderation_text
        is_violation = parsed.get("is_violation", False) if isinstance(parsed, dict) else False
        violation_types = parsed.get("violation_types", []) if isinstance(parsed, dict) else []
    except (json.JSONDecodeError, AttributeError):
        is_violation = False
        violation_types = []

    if is_violation and violation_types:
        try:
            suggestion = await community_agent_service.suggest_moderation_action(
                post.content, "、".join(violation_types)
            )
            smart_result["suggestion"] = suggestion
        except Exception as e:
            errors.append(f"审核建议失败: {str(e)}")
    else:
        smart_result["suggestion"] = {
            "suggestion": json.dumps({
                "action": "通过",
                "action_level": "none",
                "reason": "内容未检测到违规",
            }, ensure_ascii=False)
        }

    smart_result["post_id"] = post_id
    smart_result["post_title"] = post.title
    smart_result["errors"] = errors if errors else None
    return smart_result
