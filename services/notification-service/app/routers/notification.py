from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.notification_service import notification_service

router = APIRouter()


@router.get("")
async def list_notifications(
    user_id: int = Query(default=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    notification_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    notifications, total, unread_count = await notification_service.list_notifications(
        db, user_id=user_id, page=page, page_size=page_size,
        unread_only=unread_only,
    )
    items = [_notification_to_dict(n) for n in notifications]
    if notification_type:
        items = [i for i in items if i.get("type") == notification_type]
    return {
        "items": items,
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/unread-count")
async def get_unread_count(
    user_id: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
):
    count = await notification_service.get_unread_count(db, user_id=user_id)
    return {"unread_count": count}


@router.get("/{notification_id}")
async def get_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    notification = await notification_service.get_notification(db, notification_id=notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    return _notification_to_dict(notification)


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    success = await notification_service.mark_as_read(db, notification_id=notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="通知不存在")
    await db.commit()
    return {"message": "标记已读成功"}


@router.patch("/read-all")
async def mark_all_read(
    user_id: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
):
    count = await notification_service.mark_all_as_read(db, user_id=user_id)
    await db.commit()
    return {"message": "全部标记已读成功", "count": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    success = await notification_service.delete_notification(db, notification_id=notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="通知不存在")
    await db.commit()
    return {"message": "删除成功"}


@router.post("")
async def create_notification(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    notification = await notification_service.create_notification(
        db,
        user_id=body.get("user_id", 1),
        type=body.get("type", "system"),
        title=body.get("title", ""),
        content=body.get("content"),
    )
    await db.commit()
    return _notification_to_dict(notification)


@router.post("/batch-read")
async def batch_mark_read(body: dict, db: AsyncSession = Depends(get_db)):
    ids = body.get("ids", [])
    count = 0
    for nid in ids:
        success = await notification_service.mark_as_read(db, notification_id=nid)
        if success:
            count += 1
    await db.commit()
    return {"success": True, "processed_count": count}


@router.post("/batch-delete")
async def batch_delete(body: dict, db: AsyncSession = Depends(get_db)):
    ids = body.get("ids", [])
    count = 0
    for nid in ids:
        success = await notification_service.delete_notification(db, notification_id=nid)
        if success:
            count += 1
    await db.commit()
    return {"success": True, "processed_count": count}


@router.get("/types")
async def get_types_stats(
    user_id: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
):
    notifications, total, _ = await notification_service.list_notifications(
        db, user_id=user_id, page=1, page_size=1000,
    )
    type_counts: dict[str, dict] = {}
    for n in notifications:
        t = n.type
        if t not in type_counts:
            type_counts[t] = {"type": t, "total": 0, "unread": 0}
        type_counts[t]["total"] += 1
        if not n.is_read:
            type_counts[t]["unread"] += 1
    return {"stats": list(type_counts.values())}


def _notification_to_dict(n) -> dict:
    return {
        "id": n.id,
        "type": n.type,
        "title": n.title,
        "content": n.content,
        "is_read": n.is_read,
        "read_at": n.read_at.isoformat() if n.read_at else None,
        "user_id": n.user_id,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }
