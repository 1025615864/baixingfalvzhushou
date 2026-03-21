"""用户画像路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.user_service import UserService

router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取用户画像"""
    service = UserService(db)
    profile = await service.get_user_profile(user_id)

    if not profile:
        # 返回空画像
        return ProfileResponse(id=0, user_id=user_id)

    return ProfileResponse.model_validate(profile)


@router.patch("/{user_id}", response_model=ProfileResponse)
async def update_profile(
    user_id: int,
    request: ProfileUpdateRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """更新用户画像"""
    service = UserService(db)

    profile = await service.update_user_profile(
        user_id=user_id,
        nickname=request.nickname,
        avatar=request.avatar,
        bio=request.bio,
    )

    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    return ProfileResponse.model_validate(profile)
