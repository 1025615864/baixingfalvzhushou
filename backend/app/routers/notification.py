"""通知消息API路由"""
import logging
from typing import Annotated, ClassVar, cast
from typing_extensions import TypedDict

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from ..database import get_db

logger = logging.getLogger(__name__)
from ..models.notification import Notification, NotificationType
from ..models.user import User
from ..utils.deps import get_current_user, require_admin

router = APIRouter(prefix="/notifications", tags=["通知管理"])


class BatchOperationResponse(TypedDict):
    message: str
    count: int


class NotificationTypesStatsResponse(TypedDict):
    types: dict[str, int]
    type_labels: dict[str, str]


class UnreadCountResponse(TypedDict):
    unread_count: int


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    content: str | None
    link: str | None
    is_read: bool
    read_at: datetime | None = None
    related_user_id: int | None
    related_user_name: str | None = None
    created_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    unread_only: bool = False,
    notification_type: Annotated[str | None,
                                 Query(description="通知类型筛选")] = None,
):
    """获取当前用户的通知列表，支持按类型筛选"""
    query = select(Notification).where(Notification.user_id == current_user.id)

    if unread_only:
        query = query.where(Notification.is_read == False)

    if notification_type:
        query = query.where(Notification.type == notification_type)

    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 获取未读数
    unread_query = select(func.count()).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar() or 0

    # 分页查询
    query = query.order_by(Notification.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    notifications = cast(list[Notification], result.scalars().all())

    items: list[NotificationResponse] = []
    related_user_ids = [n.related_user_id for n in notifications if n.related_user_id]
    related_users_map: dict[int, str] = {}
    if related_user_ids:
        users_result = await db.execute(
            select(User.id, User.nickname, User.username)
            .where(User.id.in_(related_user_ids))
        )
        for user_id, nickname, username in users_result:
            related_users_map[user_id] = nickname or username

    for n in notifications:
        related_user_name: str | None = None
        if n.related_user_id:
            related_user_name = related_users_map.get(n.related_user_id)

        items.append(
            NotificationResponse(
                id=int(n.id),
                type=str(n.type),
                title=str(n.title),
                content=n.content,
                link=n.link,
                is_read=bool(n.is_read),
                read_at=n.read_at,
                related_user_id=n.related_user_id,
                related_user_name=related_user_name,
                created_at=n.created_at,
            )
        )

    return NotificationListResponse(
        items=items, total=total, unread_count=unread_count)


@router.get("/unread-count")
async def get_unread_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取未读通知数量"""
    result = await db.execute(
        select(func.count()).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    )
    count = result.scalar() or 0
    return {"unread_count": count}


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """标记通知为已读"""
    from datetime import datetime
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在")

    notification.is_read = True
    notification.read_at = datetime.utcnow()
    await db.commit()

    return {"message": "已标记为已读", "notification_id": notification_id}


@router.patch("/read-all")
async def mark_all_as_read(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """标记所有通知为已读"""
    from datetime import datetime
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True, read_at=datetime.utcnow())
    )
    await db.commit()

    return {"message": "已全部标记为已读"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """删除通知"""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在")

    await db.delete(notification)
    await db.commit()

    return {"message": "删除成功"}


# ============ 批量操作 ============

class BatchIdsRequest(BaseModel):
    ids: list[int]


@router.patch("/batch-read", summary="批量标记已读")
async def batch_mark_read(
    data: BatchIdsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BatchOperationResponse:
    """批量标记通知为已读"""
    if not data.ids:
        return {"message": "没有选择通知", "count": 0}

    from datetime import datetime
    _ = await db.execute(
        update(Notification)
        .where(
            Notification.id.in_(data.ids),
            Notification.user_id == current_user.id
        )
        .values(is_read=True, read_at=datetime.utcnow())
    )
    await db.commit()
    return {"message": "批量标记成功", "count": len(data.ids)}


@router.post("/batch-delete", summary="批量删除通知")
async def batch_delete(
    data: BatchIdsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BatchOperationResponse:
    """批量删除通知"""
    if not data.ids:
        return {"message": "没有选择通知", "count": 0}

    from sqlalchemy import delete
    _ = await db.execute(
        delete(Notification).where(
            Notification.id.in_(data.ids),
            Notification.user_id == current_user.id
        )
    )
    await db.commit()
    return {"message": "批量删除成功", "count": len(data.ids)}


@router.get("/types", summary="获取通知类型统计")
async def get_notification_types(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationTypesStatsResponse:
    """获取当前用户各类型通知的数量统计"""
    query = (
        select(Notification.type, func.count(Notification.id).label('count'))
        .where(Notification.user_id == current_user.id)
        .group_by(Notification.type)
    )
    result = await db.execute(query)

    type_stats: dict[str, int] = {}
    for row in result.all():
        type_key = str(cast(object, row[0]))
        type_stats[type_key] = int(cast(int, row[1]))

    return {
        "types": type_stats,
        "type_labels": {
            "comment_reply": "评论回复",
            "post_like": "点赞",
            "post_favorite": "收藏",
            "post_comment": "评论",
            "system": "系统通知",
            "consultation": "咨询相关",
            "news": "新闻订阅"
        }
    }


# ============ 管理员功能 ============

class SystemNotificationCreate(BaseModel):
    """创建系统通知"""
    title: str
    content: str
    link: str | None = None


class SystemNotificationResponse(BaseModel):
    """系统通知响应"""
    id: int
    title: str
    content: str | None
    link: str | None
    target_count: int
    created_at: datetime
    created_by: str | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class BroadcastNotificationResponse(TypedDict):
    message: str
    target_count: int


@router.post("/admin/broadcast", summary="发布系统通知（管理员）")
async def broadcast_notification(
    data: SystemNotificationCreate,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BroadcastNotificationResponse:
    """
    向所有用户发布系统通知

    - **title**: 通知标题
    - **content**: 通知内容
    - **link**: 跳转链接（可选）
    """
    # 获取所有活跃用户
    result = await db.execute(
        select(User.id).where(User.is_active)
    )
    user_ids: list[int] = [cast(int, row[0]) for row in result.fetchall()]

    if not user_ids:
        raise HTTPException(status_code=400, detail="没有可发送的目标用户")

    # 批量创建通知
    notifications: list[Notification] = []
    for user_id in user_ids:
        notification = Notification(
            user_id=user_id,
            type=NotificationType.SYSTEM,
            title=data.title,
            content=data.content,
            link=data.link,
            is_read=False,
        )
        notifications.append(notification)

    db.add_all(notifications)
    await db.commit()

    # 通过 WebSocket 推送实时通知（统一 payload）
    try:
        from ..services.unified_notification_service import unified_notification_service

        for user_id in user_ids:
            _ = await unified_notification_service.notify_ws(
                user_id=int(user_id),
                title=data.title,
                content=data.content,
                link=data.link,
                dedupe_key=None,
                notification_id=None,
            )
    except Exception:
        logger.exception("WebSocket push failed")  # WebSocket推送失败不影响主流程

    return {
        "message": "系统通知发布成功",
        "target_count": len(user_ids)
    }


class SystemNotificationsListResponse(TypedDict):
    items: list[dict[str, object]]
    total: int
    page: int
    page_size: int


@router.get("/admin/system", summary="获取系统通知列表（管理员）")
async def get_system_notifications(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SystemNotificationsListResponse:
    """获取系统通知发送记录"""
    # 获取系统通知（按创建时间分组，取每组第一条）
    query = select(Notification).where(
        Notification.type == NotificationType.SYSTEM
    ).order_by(Notification.created_at.desc())

    # 简化：直接获取唯一标题+时间的通知
    result = await db.execute(query.limit(page_size * 10))
    all_notifications = cast(list[Notification], result.scalars().all())

    # 按标题+时间去重
    seen: set[tuple[str, str]] = set()
    unique_notifications: list[Notification] = []
    for n in all_notifications:
        key = (n.title, n.created_at.strftime("%Y-%m-%d %H:%M"))
        if key not in seen:
            seen.add(key)
            unique_notifications.append(n)

    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    items: list[Notification] = unique_notifications[start:end]

    payload_items: list[dict[str, object]] = [
        {
            "id": int(n.id),
            "title": str(n.title),
            "content": n.content,
            "link": n.link,
            "created_at": n.created_at,
        }
        for n in items
    ]

    return {
        "items": payload_items,
        "total": len(unique_notifications),
        "page": page,
        "page_size": page_size,
    }


# ==================== 定向通知功能 ====================

class TargetedNotificationCreate(BaseModel):
    """定向通知创建请求"""
    title: str
    content: str | None = None
    link: str | None = None
    target_type: str  # "users", "role", "all"
    target_ids: list[int] | None = None  # 当target_type为"users"时使用
    target_role: str | None = None  # 当target_type为"role"时使用


class TargetedNotificationResponse(TypedDict):
    message: str
    target_count: int


@router.post("/admin/targeted", summary="发送定向通知（管理员）")
async def send_targeted_notification(
    data: TargetedNotificationCreate,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TargetedNotificationResponse:
    """
    向指定用户或角色发送定向通知

    - **target_type**: 目标类型 (users-指定用户, role-指定角色, all-全部用户)
    - **target_ids**: 目标用户ID列表（当target_type为users时必填）
    - **target_role**: 目标角色（当target_type为role时必填）
    """
    user_ids: list[int] = []

    if data.target_type == "users":
        if not data.target_ids:
            raise HTTPException(status_code=400, detail="请指定目标用户ID")
        # 验证用户是否存在
        result = await db.execute(
            select(User.id).where(User.id.in_(data.target_ids), User.is_active)
        )
        user_ids = [cast(int, row[0]) for row in result.fetchall()]

    elif data.target_type == "role":
        if not data.target_role:
            raise HTTPException(status_code=400, detail="请指定目标角色")
        # 根据角色获取用户（这里简化处理，实际应该查询角色关联表）
        result = await db.execute(
            select(User.id).where(
                User.is_active,
                User.role == data.target_role
            )
        )
        user_ids = [cast(int, row[0]) for row in result.fetchall()]

    elif data.target_type == "all":
        result = await db.execute(
            select(User.id).where(User.is_active)
        )
        user_ids = [cast(int, row[0]) for row in result.fetchall()]

    else:
        raise HTTPException(status_code=400, detail="无效的目标类型")

    if not user_ids:
        raise HTTPException(status_code=400, detail="没有可发送的目标用户")

    # 批量创建通知
    notifications: list[Notification] = []
    for user_id in user_ids:
        notification = Notification(
            user_id=user_id,
            type=NotificationType.SYSTEM,
            title=data.title,
            content=data.content,
            link=data.link,
            is_read=False,
        )
        notifications.append(notification)

    db.add_all(notifications)
    await db.commit()

    # 通过 WebSocket 推送实时通知
    try:
        from ..services.unified_notification_service import unified_notification_service

        for user_id in user_ids:
            _ = await unified_notification_service.notify_ws(
                user_id=int(user_id),
                title=data.title,
                content=data.content,
                link=data.link,
                dedupe_key=None,
                notification_id=None,
            )
    except Exception:
        logger.exception("WebSocket push failed")

    return {
        "message": "定向通知发送成功",
        "target_count": len(user_ids)
    }


@router.put("/admin/{notification_id}", summary="编辑系统通知（管理员）")
async def update_system_notification(
    notification_id: int,
    data: SystemNotificationCreate,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SystemNotificationResponse:
    """编辑已发送的系统通知（只更新未读的通知）"""
    # 获取该批次的所有通知（相同标题+时间的系统通知）
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.type == NotificationType.SYSTEM
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    # 更新该批次所有未读通知
    await db.execute(
        update(Notification)
        .where(
            Notification.title == notification.title,
            Notification.created_at == notification.created_at,
            Notification.type == NotificationType.SYSTEM,
            Notification.is_read == False
        )
        .values(
            title=data.title,
            content=data.content,
            link=data.link
        )
    )
    await db.commit()

    return SystemNotificationResponse(
        id=int(notification.id),
        title=data.title,
        content=data.content,
        link=data.link,
        target_count=0,
        created_at=notification.created_at,
    )


@router.delete("/admin/{notification_id}", summary="删除系统通知（管理员）")
async def delete_system_notification(
    notification_id: int,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """删除系统通知（删除该批次的所有通知）"""
    # 获取通知信息
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.type == NotificationType.SYSTEM
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    # 删除该批次所有通知
    await db.execute(
        delete(Notification).where(
            Notification.title == notification.title,
            Notification.created_at == notification.created_at,
            Notification.type == NotificationType.SYSTEM
        )
    )
    await db.commit()

    return {"message": "通知已删除", "notification_id": str(notification_id)}
