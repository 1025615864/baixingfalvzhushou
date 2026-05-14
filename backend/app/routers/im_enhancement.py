"""IM 增强 API 路由 - 离线消息、会话管理、快捷回复"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from ..middleware.auth import get_current_user, AuthUser
from ..services.im_enhancement import (
    offline_queue,
    session_tracker,
    get_pending_messages_for_user,
    get_pending_message_count,
)
from ..schemas.response import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class QuickReplyRequest(BaseModel):
    consultation_id: int
    template_id: int


@router.get("/im/offline-messages")
async def get_offline_messages(
    current_user: AuthUser = Depends(get_current_user),
):
    """获取离线消息"""
    messages = get_pending_messages_for_user(current_user.id)
    return ApiResponse.success({
        "user_id": current_user.id,
        "messages": messages,
        "count": len(messages),
    })


@router.get("/im/pending-count")
async def get_pending_count(
    current_user: AuthUser = Depends(get_current_user),
):
    """获取待推送消息数量"""
    count = get_pending_message_count(current_user.id)
    return ApiResponse.success({"user_id": current_user.id, "pending_count": count})


@router.post("/im/sessions/{consultation_id}/start")
async def start_chat_session(
    consultation_id: int,
    lawyer_id: int = Query(...),
    current_user: AuthUser = Depends(get_current_user),
):
    """开始跟踪聊天会话"""
    session_tracker.start_session(
        consultation_id=consultation_id,
        lawyer_id=lawyer_id,
        user_id=current_user.id,
    )
    return ApiResponse.success({
        "consultation_id": consultation_id,
        "status": "tracking",
        "timeout_minutes": session_tracker.SESSION_TIMEOUT_MINUTES,
    })


@router.post("/im/sessions/{consultation_id}/activity")
async def record_session_activity(
    consultation_id: int,
    current_user: AuthUser = Depends(get_current_user),
):
    """记录会话活动（每次消息发送时调用）"""
    session_tracker.record_activity(consultation_id)
    session = session_tracker.get_session_status(consultation_id)
    return ApiResponse.success({"consultation_id": consultation_id, "session": session})


@router.get("/im/sessions/{consultation_id}/status")
async def get_session_status(
    consultation_id: int,
    current_user: AuthUser = Depends(get_current_user),
):
    """获取会话状态"""
    session = session_tracker.get_session_status(consultation_id)
    if not session:
        return ApiResponse.success({
            "consultation_id": consultation_id,
            "status": "not_tracked",
        })
    return ApiResponse.success({"consultation_id": consultation_id, "session": session})


@router.post("/im/sessions/{consultation_id}/close")
async def close_chat_session(
    consultation_id: int,
    current_user: AuthUser = Depends(get_current_user),
):
    """关闭聊天会话（触发评价提醒）"""
    session = session_tracker.close_session(consultation_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或已关闭")

    return ApiResponse.success({
        "consultation_id": consultation_id,
        "status": "closed",
        "duration_seconds": session.get("duration", 0),
        "message": "会话已关闭，请评价律师服务",
        "evaluation_url": f"/consultations/{consultation_id}/review",
    })


@router.get("/im/sessions/active")
async def get_active_sessions(
    current_user: AuthUser = Depends(get_current_user),
):
    """获取活跃会话列表"""
    active = session_tracker.get_active_sessions()
    return ApiResponse.success({"active_sessions": active, "count": len(active)})


@router.get("/im/quick-reply-templates")
async def get_quick_reply_templates(
    lawyer_id: Optional[int] = Query(None),
    current_user: AuthUser = Depends(get_current_user),
):
    """获取快捷回复模板（用于 IM 聊天中一键使用）"""
    import httpx

    try:
        target_lawyer_id = lawyer_id or current_user.id
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"http://legal-service:8008/api/v1/legal/lawyers/{target_lawyer_id}/reply-templates"
            )
            if resp.status_code == 200:
                data = resp.json()
                templates = data.get("items", data.get("templates", []))
                return ApiResponse.success({
                    "lawyer_id": target_lawyer_id,
                    "templates": templates,
                    "total": len(templates),
                })
            return ApiResponse.success({"lawyer_id": target_lawyer_id, "templates": [], "total": 0})
    except Exception as e:
        logger.warning(f"获取快捷回复模板失败: {e}")
        return ApiResponse.success({"lawyer_id": target_lawyer_id, "templates": [], "total": 0})