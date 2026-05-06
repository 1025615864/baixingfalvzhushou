"""用户画像路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.user_service import UserService
from ..services.avatar_service import AvatarService
from ..middleware.auth import get_current_user

router = APIRouter()


class ProfileCreateRequest(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """获取用户画像"""
    service = UserService(db)
    profile = await service.get_user_profile(user_id)

    if not profile:
        return ProfileResponse(id=0, user_id=user_id)

    return ProfileResponse.model_validate(profile)


@router.post("/", response_model=ProfileResponse)
async def create_profile(
    request: ProfileCreateRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """创建用户画像"""
    if request.avatar is not None:
        is_valid, error_msg = AvatarService.validate_avatar_url(request.avatar)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid avatar URL: {error_msg}")

    service = UserService(db)

    existing = await service.get_user_profile(current_user.id)
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")

    profile = await service.create_user_profile(
        user_id=current_user.id,
        nickname=request.nickname,
        avatar=request.avatar,
        bio=request.bio,
        gender=request.gender,
        birthday=request.birthday,
        province=request.province,
        city=request.city,
    )

    return ProfileResponse.model_validate(profile)


@router.patch("/{user_id}", response_model=ProfileResponse)
async def update_profile(
    user_id: int = Path(..., ge=1),
    request: ProfileUpdateRequest = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """更新用户画像"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")

    if request.avatar is not None:
        is_valid, error_msg = AvatarService.validate_avatar_url(request.avatar)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid avatar URL: {error_msg}")

    service = UserService(db)

    profile = await service.update_user_profile(
        user_id=user_id,
        nickname=request.nickname,
        avatar=request.avatar,
        bio=request.bio,
        gender=request.gender,
        birthday=request.birthday,
        province=request.province,
        city=request.city,
    )

    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    return ProfileResponse.model_validate(profile)


@router.delete("/{user_id}")
async def delete_profile(
    user_id: int = Path(..., ge=1),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """删除用户画像"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this profile")

    service = UserService(db)
    success = await service.delete_user_profile(user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {"message": "Profile deleted successfully"}


class AvatarValidationRequest(BaseModel):
    avatar_url: str


class AvatarValidationResponse(BaseModel):
    valid: bool
    avatar_url: Optional[str] = None
    error: Optional[str] = None


@router.post("/avatar/validate", response_model=AvatarValidationResponse)
async def validate_avatar(
    request: AvatarValidationRequest,
    current_user = Depends(get_current_user),
):
    """验证头像URL

    验证头像URL格式是否正确，返回验证结果。
    支持的格式: jpg, png, gif, webp, svg
    """
    is_valid, error_msg = AvatarService.validate_avatar_url(request.avatar_url)

    if is_valid:
        return AvatarValidationResponse(
            valid=True,
            avatar_url=request.avatar_url,
        )
    else:
        return AvatarValidationResponse(
            valid=False,
            error=error_msg,
        )


@router.post("/avatar/default", response_model=AvatarValidationResponse)
async def get_default_avatar(
    current_user = Depends(get_current_user),
):
    """获取默认头像URL

    根据用户ID生成默认头像URL。
    """
    default_url = AvatarService.generate_default_avatar(
        user_id=current_user.id,
        nickname=None,
    )

    return AvatarValidationResponse(
        valid=True,
        avatar_url=default_url,
    )
