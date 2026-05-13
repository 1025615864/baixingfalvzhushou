"""通知系统 API 路由"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database.session import get_db
from ..models import Notification

router = APIRouter(prefix="/notifications", tags=["Notification"])


class BatchIdsBody(BaseModel):
    ids: list[int]


class CreateSystemNotificationBody(BaseModel):
    title: str
    content: str
    target_type: str = "all"
    target_ids: Optional[list[str]] = None
    expires_at: Optional[str] = None


class UpdateSystemNotificationBody(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_type: Optional[str] = None
    target_ids: Optional[list[str]] = None
    is_published: Optional[bool] = None
    expires_at: Optional[str] = None


_mock_notifications: list[dict] = [
    {"id": 1, "user_id": 1001, "notification_type": "consultation", "title": "咨询已确认", "content": "您与张律师的法律咨询已确认，请按时参加。", "is_read": False, "target_id": "1", "created_at": (datetime.now() - timedelta(hours=1)).isoformat()},
    {"id": 2, "user_id": 1001, "notification_type": "system", "title": "系统维护通知", "content": "系统将于今晚22:00-24:00进行维护升级。", "is_read": False, "target_id": None, "created_at": (datetime.now() - timedelta(hours=3)).isoformat()},
    {"id": 3, "user_id": 1001, "notification_type": "payment", "title": "支付成功", "content": "您已成功支付咨询费500元。", "is_read": True, "target_id": "ORD20250501001", "created_at": (datetime.now() - timedelta(days=1)).isoformat()},
    {"id": 4, "user_id": 1001, "notification_type": "review", "title": "请评价服务", "content": "您的咨询已完成，请对律师服务进行评价。", "is_read": False, "target_id": "1", "created_at": (datetime.now() - timedelta(days=1)).isoformat()},
    {"id": 5, "user_id": 1001, "notification_type": "promotion", "title": "邀请奖励到账", "content": "您邀请的用户已注册，获得50积分奖励。", "is_read": True, "target_id": None, "created_at": (datetime.now() - timedelta(days=2)).isoformat()},
    {"id": 6, "user_id": 1001, "notification_type": "points", "title": "积分变动通知", "content": "您通过每日签到获得10积分。", "is_read": True, "target_id": None, "created_at": (datetime.now() - timedelta(days=3)).isoformat()},
    {"id": 7, "user_id": 1001, "notification_type": "system", "title": "新功能上线", "content": "律师主页功能已上线，快去设置专属主页吧！", "is_read": False, "target_id": None, "created_at": (datetime.now() - timedelta(days=4)).isoformat()},
    {"id": 8, "user_id": 1001, "notification_type": "consultation", "title": "咨询提醒", "content": "您明天下午2点有安排好的法律咨询。", "is_read": False, "target_id": "2", "created_at": (datetime.now() - timedelta(days=5)).isoformat()},
    {"id": 9, "user_id": 1001, "notification_type": "payment", "title": "退款通知", "content": "已取消的咨询费用已退回原支付方式。", "is_read": True, "target_id": "ORD20250503001", "created_at": (datetime.now() - timedelta(days=6)).isoformat()},
    {"id": 10, "user_id": 1001, "notification_type": "points", "title": "积分即将过期", "content": "您有200积分将在30天后过期，请尽快使用。", "is_read": False, "target_id": None, "created_at": (datetime.now() - timedelta(days=7)).isoformat()},
]

_system_notifications: list[dict] = [
    {"id": 1, "title": "法律知识库更新公告", "content": "知识库已新增100+法律法规条目，欢迎查阅。", "target_type": "all", "target_ids": None, "sent_count": 2580, "read_count": 890, "is_published": True, "published_at": "2025-05-01T09:00:00", "expires_at": None, "created_by": "admin", "created_at": "2025-05-01T09:00:00", "updated_at": "2025-05-01T09:00:00"},
    {"id": 2, "title": "律师认证审核通知", "content": "请各位律师尽快完成执业认证，逾期将影响服务。", "target_type": "lawyers", "target_ids": None, "sent_count": 560, "read_count": 420, "is_published": True, "published_at": "2025-04-15T10:00:00", "expires_at": "2025-06-01T00:00:00", "created_by": "admin", "created_at": "2025-04-15T10:00:00", "updated_at": "2025-04-15T10:00:00"},
    {"id": 3, "title": "五一假期服务调整通知", "content": "五一期间在线咨询正常服务，电话咨询暂停。", "target_type": "all", "target_ids": None, "sent_count": 3200, "read_count": 2100, "is_published": True, "published_at": "2025-04-28T14:00:00", "expires_at": "2025-05-06T00:00:00", "created_by": "admin", "created_at": "2025-04-28T14:00:00", "updated_at": "2025-04-28T14:00:00"},
]

_next_system_id = 4


def _paginate(data: list[dict], page: int, page_size: int) -> dict:
    total = len(data)
    start = (page - 1) * page_size
    items = data[start:start + page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("")
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    notification_type: Optional[str] = Query(None),
):
    data = list(_mock_notifications)
    if unread_only:
        data = [n for n in data if not n["is_read"]]
    if notification_type:
        data = [n for n in data if n["notification_type"] == notification_type]
    return _paginate(data, page, page_size)


@router.get("/unread-count")
async def get_unread_count():
    count = sum(1 for n in _mock_notifications if not n["is_read"])
    return {"count": count}


@router.patch("/{notification_id}/read")
async def mark_as_read(notification_id: int):
    for n in _mock_notifications:
        if n["id"] == notification_id:
            n["is_read"] = True
            return {"message": "已标记为已读"}
    return {"detail": "通知不存在"}


@router.patch("/read-all")
async def mark_all_as_read():
    for n in _mock_notifications:
        n["is_read"] = True
    return {"message": "全部标记为已读"}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: int):
    global _mock_notifications
    _mock_notifications = [n for n in _mock_notifications if n["id"] != notification_id]
    return {"message": "已删除"}


@router.post("/batch-read")
async def batch_mark_read(body: BatchIdsBody):
    count = 0
    for n in _mock_notifications:
        if n["id"] in body.ids and not n["is_read"]:
            n["is_read"] = True
            count += 1
    return {"success_count": count, "failed_count": 0, "message": f"已标记{count}条为已读"}


@router.post("/batch-delete")
async def batch_delete(body: BatchIdsBody):
    global _mock_notifications
    before = len(_mock_notifications)
    _mock_notifications = [n for n in _mock_notifications if n["id"] not in body.ids]
    return {"success_count": before - len(_mock_notifications), "failed_count": 0, "message": f"已删除{before - len(_mock_notifications)}条"}


@router.get("/types")
async def get_notification_types():
    types: dict[str, int] = {}
    for n in _mock_notifications:
        types[n["notification_type"]] = types.get(n["notification_type"], 0) + 1
    return {"types": types}


# ==========================================
# 系统通知管理（管理员）
# ==========================================

admin_router = APIRouter(prefix="/v1/admin/notifications", tags=["System-Notifications"])


@admin_router.get("")
async def get_system_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_published: Optional[bool] = Query(None),
    keyword: Optional[str] = Query(None),
):
    data = list(_system_notifications)
    if is_published is not None:
        data = [s for s in data if s["is_published"] == is_published]
    if keyword:
        kw = keyword.lower()
        data = [s for s in data if kw in s["title"].lower() or kw in s["content"].lower()]
    return _paginate(data, page, page_size)


@admin_router.post("")
async def create_system_notification(body: CreateSystemNotificationBody, db: AsyncSession = Depends(get_db)):
    global _next_system_id
    now = datetime.now().isoformat()
    item = {
        "id": _next_system_id, "title": body.title, "content": body.content,
        "target_type": body.target_type, "target_ids": body.target_ids,
        "sent_count": 0, "read_count": 0, "is_published": False,
        "published_at": None, "expires_at": body.expires_at,
        "created_by": "admin", "created_at": now, "updated_at": now,
    }
    _next_system_id += 1
    _system_notifications.append(item)
    try:
        db_notification = Notification(
            user_id=1, type="system", title=body.title,
            content=body.content,
        )
        db.add(db_notification)
        await db.commit()
    except Exception:
        pass
    return item


@admin_router.put("/{notification_id}")
async def update_system_notification(notification_id: int, body: UpdateSystemNotificationBody):
    for item in _system_notifications:
        if item["id"] == notification_id:
            for field, value in body.model_dump(exclude_none=True).items():
                item[field] = value
            item["updated_at"] = datetime.now().isoformat()
            return item
    return {"detail": "系统通知不存在"}


@admin_router.delete("/{notification_id}")
async def delete_system_notification(notification_id: int):
    global _system_notifications
    _system_notifications = [s for s in _system_notifications if s["id"] != notification_id]
    return {"message": "已删除"}