"""通知路由"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_notifications(user_id: int, page: int = 1, page_size: int = 20):
    return {"items": [], "total": 0}


@router.put("/{notification_id}/read")
async def mark_as_read(notification_id: int):
    return {"success": True}


@router.post("/settings")
async def update_settings(user_id: int, email_enabled: bool = True, sms_enabled: bool = True):
    return {"success": True}
