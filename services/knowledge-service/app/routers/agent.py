"""知识库运营助手 Agent 路由 - AI辅助质量评估/关联推荐/关键词提取/分类建议"""
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.knowledge_agent_service import knowledge_agent_service
from app.database import get_db
from app.models.knowledge import LegalKnowledge

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from typing import List, Set

    _security = HTTPBearer(auto_error=False)

    GLOBAL_ADMIN_ROLES = {"super_admin", "admin"}

    DOMAIN_ROLES: dict[str, Set[str]] = {
        "global": {"super_admin", "admin"},
        "knowledge": {"knowledge_admin", "knowledge_ops"},
    }

    class AdminUser:
        def __init__(self, user_id: int, role: str, permissions: Optional[List[str]] = None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in GLOBAL_ADMIN_ROLES

        def has_domain_access(self, domain: str) -> bool:
            if self.is_super_admin:
                return True
            return self.role in DOMAIN_ROLES.get(domain, set())

    async def get_admin_user(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> AdminUser:
        if not credentials:
            raise HTTPException(status_code=401, detail="未提供认证凭据")
        return AdminUser(user_id=1, role="admin", permissions=[])

    def require_domain_role(domain: str, roles: Optional[List[str]] = None):
        async def domain_checker(admin: AdminUser = Depends(get_admin_user)):
            if admin.is_super_admin:
                return admin
            if not admin.has_domain_access(domain):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要 {domain} 域管理角色，当前角色: {admin.role}",
                )
            if roles and admin.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要角色: {', '.join(roles)}，当前角色: {admin.role}",
                )
            return admin
        return domain_checker


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["AI运营助手"], dependencies=[Depends(require_domain_role("knowledge"))])


class EvaluateQualityRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10, max_length=20000)


class RecommendRelatedRequest(BaseModel):
    knowledge_id: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10, max_length=20000)


class GenerateKeywordsRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10, max_length=20000)


class SuggestCategoryRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10, max_length=20000)


@router.post("/evaluate-quality")
async def evaluate_quality(
    body: EvaluateQualityRequest,
    _admin: AdminUser = Depends(get_admin_user),
):
    """AI知识质量评估 - 自动评分与改进建议"""
    try:
        result = await knowledge_agent_service.evaluate_quality(body.title, body.content)
        return result
    except Exception as e:
        logger.error(f"AI quality evaluation failed: {e}")
        raise HTTPException(status_code=500, detail="AI质量评估失败，请稍后重试")


@router.post("/recommend-related")
async def recommend_related(
    body: RecommendRelatedRequest,
    _admin: AdminUser = Depends(get_admin_user),
):
    """AI知识关联推荐 - 自动发现相关知识条目"""
    try:
        result = await knowledge_agent_service.recommend_related(
            body.knowledge_id, body.title, body.content
        )
        return result
    except Exception as e:
        logger.error(f"AI related recommendation failed: {e}")
        raise HTTPException(status_code=500, detail="AI关联推荐失败，请稍后重试")


@router.post("/generate-keywords")
async def generate_keywords(
    body: GenerateKeywordsRequest,
    _admin: AdminUser = Depends(get_admin_user),
):
    """AI关键词提取 - 自动提取法律关键词"""
    try:
        result = await knowledge_agent_service.generate_keywords(body.title, body.content)
        return result
    except Exception as e:
        logger.error(f"AI keyword generation failed: {e}")
        raise HTTPException(status_code=500, detail="AI关键词提取失败，请稍后重试")


@router.post("/suggest-category")
async def suggest_category(
    body: SuggestCategoryRequest,
    _admin: AdminUser = Depends(get_admin_user),
):
    """AI分类建议 - 推荐最合适的知识分类"""
    try:
        result = await knowledge_agent_service.suggest_category(body.title, body.content)
        return result
    except Exception as e:
        logger.error(f"AI category suggestion failed: {e}")
        raise HTTPException(status_code=500, detail="AI分类建议失败，请稍后重试")


@router.post("/knowledge/{knowledge_id}/smart-evaluate")
async def smart_evaluate(
    knowledge_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_admin_user),
):
    """AI一键智能评估 - 综合评估+关键词+分类"""
    knowledge = db.query(LegalKnowledge).filter(LegalKnowledge.id == knowledge_id).first()
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识条目不存在")

    title = knowledge.title
    content = knowledge.content or ""
    result = {}
    errors = []

    try:
        evaluation = await knowledge_agent_service.evaluate_quality(title, content)
        result["evaluation"] = evaluation
    except Exception as e:
        errors.append(f"质量评估失败: {str(e)}")

    try:
        keywords = await knowledge_agent_service.generate_keywords(title, content)
        result["keywords"] = keywords
    except Exception as e:
        errors.append(f"关键词提取失败: {str(e)}")

    try:
        category = await knowledge_agent_service.suggest_category(title, content)
        result["category"] = category
    except Exception as e:
        errors.append(f"分类建议失败: {str(e)}")

    result["knowledge_id"] = knowledge_id
    result["title"] = title
    result["errors"] = errors if errors else None
    return result
