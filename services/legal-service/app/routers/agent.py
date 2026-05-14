"""法律运营助手 Agent 路由 - AI辅助律师匹配/咨询分析/风险识别/回复建议/推荐优化"""
from typing import Optional, Dict, Any, List

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.services.legal_agent_service import legal_agent_service
from app.database import get_db, AsyncSession
from app.models.consultation import Consultation, ChatMessage

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    import os
    from fastapi import HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from typing import List, Set

    _security = HTTPBearer(auto_error=False)

    GLOBAL_ADMIN_ROLES = {"super_admin", "admin"}

    DOMAIN_ROLES: dict[str, Set[str]] = {
        "global": {"super_admin", "admin"},
        "legal": {"legal_admin", "legal_ops", "lawfirm_owner"},
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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证凭据")
        if os.getenv("DISABLE_AUTH", "").lower() in {"1", "true", "yes"}:
            return AdminUser(user_id=0, role="admin")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证服务不可用")

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

router = APIRouter()


class MatchLawyerRequest(BaseModel):
    consultation_content: str = Field(..., min_length=10, max_length=10000)
    category: str = Field(..., min_length=1, max_length=50)


class ConsultationSummaryRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=20000)


class AnalyzeRiskRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=20000)


class SuggestResponseRequest(BaseModel):
    consultation_content: str = Field(..., min_length=10, max_length=10000)
    category: str = Field(..., min_length=1, max_length=50)


class OptimizeRecommendationRequest(BaseModel):
    history_data: Dict[str, Any] = Field(...)


@router.post("/match-lawyer")
async def match_lawyer(
    body: MatchLawyerRequest,
    admin: AdminUser = Depends(require_domain_role("legal")),
):
    try:
        result = await legal_agent_service.match_lawyer(body.consultation_content, body.category)
        return result
    except Exception as e:
        logger.error(f"AI lawyer matching failed: {e}")
        raise HTTPException(status_code=500, detail="AI律师匹配失败，请稍后重试")


@router.post("/consultation-summary")
async def consultation_summary(
    body: ConsultationSummaryRequest,
    admin: AdminUser = Depends(require_domain_role("legal")),
):
    try:
        result = await legal_agent_service.generate_consultation_summary(body.content)
        return result
    except Exception as e:
        logger.error(f"AI consultation summary failed: {e}")
        raise HTTPException(status_code=500, detail="AI咨询摘要生成失败，请稍后重试")


@router.post("/analyze-risk")
async def analyze_risk(
    body: AnalyzeRiskRequest,
    admin: AdminUser = Depends(require_domain_role("legal")),
):
    try:
        result = await legal_agent_service.analyze_legal_risk(body.content)
        return result
    except Exception as e:
        logger.error(f"AI legal risk analysis failed: {e}")
        raise HTTPException(status_code=500, detail="AI法律风险分析失败，请稍后重试")


@router.post("/suggest-response")
async def suggest_response(
    body: SuggestResponseRequest,
    admin: AdminUser = Depends(require_domain_role("legal")),
):
    try:
        result = await legal_agent_service.suggest_response(body.consultation_content, body.category)
        return result
    except Exception as e:
        logger.error(f"AI response suggestion failed: {e}")
        raise HTTPException(status_code=500, detail="AI回复建议生成失败，请稍后重试")


@router.post("/optimize-recommendation")
async def optimize_recommendation(
    body: OptimizeRecommendationRequest,
    admin: AdminUser = Depends(require_domain_role("legal")),
):
    try:
        result = await legal_agent_service.optimize_recommendation(body.history_data)
        return result
    except Exception as e:
        logger.error(f"AI recommendation optimization failed: {e}")
        raise HTTPException(status_code=500, detail="AI推荐优化失败，请稍后重试")


@router.post("/consultations/{consultation_id}/smart-analyze")
async def smart_analyze_consultation(
    consultation_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_domain_role("legal")),
):
    result_stmt = await db.execute(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    consultation = result_stmt.scalar_one_or_none()
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询不存在")

    content_parts = [f"标题：{consultation.title}", f"描述：{consultation.description}"]

    msg_stmt = await db.execute(
        select(ChatMessage.content)
        .where(ChatMessage.consultation_id == consultation_id)
        .order_by(ChatMessage.created_at)
    )
    messages = msg_stmt.scalars().all()
    if messages:
        content_parts.append("对话记录：" + "\n".join(messages))

    full_content = "\n".join(content_parts)
    category = consultation.category or "其他"

    analyze_result = {}
    errors = []

    try:
        match = await legal_agent_service.match_lawyer(full_content, category)
        analyze_result["lawyer_match"] = match
    except Exception as e:
        errors.append(f"律师匹配失败: {str(e)}")

    try:
        summary = await legal_agent_service.generate_consultation_summary(full_content)
        analyze_result["consultation_summary"] = summary
    except Exception as e:
        errors.append(f"咨询摘要失败: {str(e)}")

    try:
        risk = await legal_agent_service.analyze_legal_risk(full_content)
        analyze_result["risk_analysis"] = risk
    except Exception as e:
        errors.append(f"风险分析失败: {str(e)}")

    try:
        suggestion = await legal_agent_service.suggest_response(full_content, category)
        analyze_result["response_suggestion"] = suggestion
    except Exception as e:
        errors.append(f"回复建议失败: {str(e)}")

    analyze_result["consultation_id"] = consultation_id
    analyze_result["category"] = category
    analyze_result["errors"] = errors if errors else None
    return analyze_result
