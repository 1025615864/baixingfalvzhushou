"""视频咨询路由"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import AsyncSessionLocal
from ..models.consultation import Consultation
from ..models.video import VideoConsultation
from ..middleware.auth import get_current_user, get_current_lawyer, AuthUser
from ..schemas.response import ApiResponse

router = APIRouter()


@router.post("/book")
async def book_video(
    consultation_id: int,
    scheduled_start: datetime,
    scheduled_end: datetime,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """创建视频咨询预约"""
    consultation = await db.get(Consultation, consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询不存在")

    existing = await db.scalar(
        select(VideoConsultation).where(
            VideoConsultation.consultation_id == consultation_id
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="该咨询已有视频预约")

    room_id = f"ROOM-{uuid.uuid4().hex[:12].upper()}"

    video = VideoConsultation(
        consultation_id=consultation_id,
        room_id=room_id,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    return ApiResponse.success({
        "id": video.id,
        "consultation_id": consultation_id,
        "room_id": room_id,
        "status": video.status,
        "scheduled_start": video.scheduled_start.isoformat() if video.scheduled_start else None,
        "scheduled_end": video.scheduled_end.isoformat() if video.scheduled_end else None,
    })


@router.get("/room-signature")
async def get_room_signature(
    consultation_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """生成 TRTC 房间签名"""
    video = await db.scalar(
        select(VideoConsultation).where(
            VideoConsultation.consultation_id == consultation_id
        )
    )
    if not video:
        raise HTTPException(status_code=404, detail="视频预约不存在")
    if video.status == "cancelled":
        raise HTTPException(status_code=400, detail="视频已取消")

    signature = f"sig_{uuid.uuid4().hex[:20]}"

    return ApiResponse.success({
        "room_id": video.room_id,
        "signature": signature,
        "user_id": str(current_user.id),
        "expire_at": (datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat(),
    })


@router.post("/{video_id}/start")
async def start_video(
    video_id: int,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """开始视频通话"""
    video = await db.get(VideoConsultation, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="视频预约不存在")

    video.status = "in_progress"
    video.started_at = datetime.utcnow()
    await db.commit()

    return ApiResponse.success({
        "id": video.id,
        "room_id": video.room_id,
        "status": "in_progress",
        "started_at": video.started_at.isoformat() if video.started_at else None,
    })


@router.post("/end")
async def end_video(
    consultation_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """结束视频通话"""
    video = await db.scalar(
        select(VideoConsultation).where(
            VideoConsultation.consultation_id == consultation_id
        )
    )
    if not video:
        raise HTTPException(status_code=404, detail="视频预约不存在")

    now = datetime.utcnow()
    video.status = "ended"
    video.ended_at = now
    if video.started_at:
        video.duration = int((now - video.started_at).total_seconds())

    video.recording_url = f"https://recordings.example.com/{video.room_id}.mp4"
    await db.commit()

    return ApiResponse.success({
        "id": video.id,
        "room_id": video.room_id,
        "status": "ended",
        "duration": video.duration,
        "recording_url": video.recording_url,
    })


@router.get("/{consultation_id}")
async def get_video_by_consultation(
    consultation_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取咨询的视频记录"""
    video = await db.scalar(
        select(VideoConsultation).where(
            VideoConsultation.consultation_id == consultation_id
        )
    )
    if not video:
        raise HTTPException(status_code=404, detail="视频记录不存在")

    return ApiResponse.success({
        "id": video.id,
        "consultation_id": video.consultation_id,
        "room_id": video.room_id,
        "status": video.status,
        "scheduled_start": video.scheduled_start.isoformat() if video.scheduled_start else None,
        "scheduled_end": video.scheduled_end.isoformat() if video.scheduled_end else None,
        "started_at": video.started_at.isoformat() if video.started_at else None,
        "ended_at": video.ended_at.isoformat() if video.ended_at else None,
        "duration": video.duration,
        "recording_url": video.recording_url,
    })