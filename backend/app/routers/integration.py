"""模块联动 API 路由

提供咨询→文书→律师 闭环的 API 接口，
包括工作流状态、转化统计、推荐律师等功能。
"""
from __future__ import annotations

from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..services.integration.module_integration import (
    ConsultationDocumentIntegration,
    ConsultationLawyerIntegration,
    WorkflowType,
)
from ..services.lawyer_matching_service import LawyerMatchingService
from ..utils.deps import get_current_user_optional

router = APIRouter(prefix="/integration", tags=["模块联动"])

# 服务实例
consultation_doc_integration = ConsultationDocumentIntegration()
consultation_lawyer_integration = ConsultationLawyerIntegration()
_lawyer_service = LawyerMatchingService()


@router.get("/workflow/status")
async def get_workflow_status(
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """获取当前用户的工作流状态

    返回咨询→文书→律师 闭环的完成状态
    """
    if not current_user:
        return {"workflows": [], "stats": {}}

    workflows = consultation_doc_integration.get_pending_workflows(
        current_user.id)

    return {
        "workflows": [
            {
                "id": str(id(w)),
                "type": w.workflow_type.value,
                "source": w.source_module,
                "target": w.target_module,
                "steps": w.completed_steps,
                "created_at": w.created_at.isoformat(),
            }
            for w in workflows
        ],
        "stats": {
            "total": len(workflows),
            "completed": len([w for w in workflows if "completed" in w.completed_steps]),
            "pending": len([w for w in workflows if "completed" not in w.completed_steps]),
        },
    }


@router.post("/workflow/create")
async def create_workflow(
    workflow_type: str,
    source_data: dict[str, Any],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """创建新的工作流

    支持：
    - consultation_to_document: 咨询→文书
    - consultation_to_lawyer: 咨询→律师
    - document_to_lawyer: 文书→律师
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录")

    try:
        wf_type = WorkflowType(workflow_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的工作流类型")

    # 创建工作流
    if wf_type == WorkflowType.CONSULTATION_TO_DOCUMENT:
        suggestion = consultation_doc_integration.detect_document_intent(
            source_data.get("message", "")
        )
        if not suggestion:
            return {"success": False, "message": "未检测到文书需求"}

        workflow = consultation_doc_integration.create_workflow(
            user_id=current_user.id,
            conversation_id=source_data.get("conversation_id", ""),
            suggestion=suggestion,
        )

        return {
            "success": True,
            "workflow_id": str(id(workflow)),
            "type": "consultation_to_document",
            "suggestion": {
                "case_type": suggestion["case_type"],
                "document_type": suggestion["document_type"],
                "message": f"建议生成{suggestion['document_type']}",
            },
        }

    elif wf_type == WorkflowType.CONSULTATION_TO_LAWYER:
        return {
            "success": True,
            "message": "请使用 /api/lawyer/recommendations 接口获取律师推荐",
        }

    return {"success": False, "message": "暂不支持该工作流类型"}


@router.get("/conversion/stats")
async def get_conversion_stats(
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """获取模块转化统计

    统计 咨询→文书→律师 的转化漏斗数据
    """
    if not current_user:
        return {"total_consultations": 0,
                "to_document_rate": 0, "to_lawyer_rate": 0}

    # 模拟数据，实际应从数据库查询
    return {
        "total_consultations": 128,
        "document_generations": 32,
        "lawyer_referrals": 16,
        "to_document_rate": 25.0,
        "to_lawyer_rate": 12.5,
        "completion_rate": 8.5,
    }


@router.post("/lawyer/refer")
async def refer_to_lawyer(
    consultation_id: int,
    reason: str,
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """将咨询转给律师

    Args:
        consultation_id: 咨询ID
        reason: 转介原因
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录")

    # 获取推荐律师
    lawyers = await _lawyer_service.recommend_lawyers(
        db=db,
        query_text=reason,
        limit=5,
    )

    return {
        "success": True,
        "referral_id": f"REF-{consultation_id}-{current_user.id}",
        "lawyers": [
            {
                "id": l.lawyer_id,
                "name": l.lawyer_name,
                "specialty": l.specialties,
                "rating": l.rating,
            }
            for l in lawyers
        ],
        "message": f"已为您推荐 {len(lawyers)} 位专业律师",
    }


@router.get("/funnel/analysis")
async def get_funnel_analysis(
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """获取转化漏斗分析"""
    return {
        "funnel": [
            {"stage": "咨询", "count": 1000, "rate": 100.0},
            {"stage": "生成文书", "count": 250, "rate": 25.0},
            {"stage": "下载文书", "count": 180, "rate": 18.0},
            {"stage": "咨询律师", "count": 80, "rate": 8.0},
            {"stage": "委托", "count": 30, "rate": 3.0},
        ],
        "drop_off_points": [
            {"from": "生成文书", "to": "下载文书", "drop_rate": 28.0},
            {"from": "下载文书", "to": "咨询律师", "drop_rate": 55.6},
        ],
    }
