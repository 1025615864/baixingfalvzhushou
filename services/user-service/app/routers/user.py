"""用户路由"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import AsyncSessionLocal
from ..models import User, UserProfile
from ..services.user_service import UserService
from ..middleware.auth import get_current_user, require_admin

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    uid: str
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    role: str
    status: str
    is_active: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


async def _get_user_with_profile(db: AsyncSession, user: User) -> dict:
    """获取用户信息并合并Profile数据"""
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()

    return {
        "id": user.id,
        "uid": user.uid,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "nickname": profile.nickname if profile else None,
        "avatar": profile.avatar if profile else None,
        "role": user.role,
        "status": user.status,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


async def _get_user_by_uid(db: AsyncSession, uid: str) -> Optional[dict]:
    """根据uid获取用户信息（合并Profile）"""
    result = await db.execute(
        select(User).where(User.uid == uid)
    )
    user = result.scalar_one_or_none()

    if not user:
        return None

    return await _get_user_with_profile(db, user)


async def _list_users_with_profiles(db: AsyncSession, skip: int, limit: int, role: Optional[str]) -> tuple[list[dict], int]:
    """获取用户列表（合并Profile数据）"""
    query = select(User)
    count_query = select(func.count(User.id))

    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    users = list(result.scalars().all())

    items = []
    for user in users:
        items.append(await _get_user_with_profile(db, user))

    return items, total


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """获取当前用户信息"""
    return await _get_user_with_profile(db, current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """更新当前用户信息（仅限User核心字段）"""
    service = UserService(db)
    user = await service.update_user(
        user_id=current_user.id,
        username=request.username,
        email=request.email,
        phone=request.phone,
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await _get_user_with_profile(db, user)


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """获取用户列表（分页，仅管理员）"""
    skip = (page - 1) * page_size

    items, total = await _list_users_with_profiles(db, skip, page_size, role)

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/uid/{uid}", response_model=UserResponse)
async def get_user_by_uid(
    uid: str,
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """根据UID获取用户详情（对外唯一标识）"""
    user_data = await _get_user_by_uid(db, uid)

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(user_data)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """根据ID获取用户详情（内部使用）"""
    service = UserService(db)
    user = await service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await _get_user_with_profile(db, user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int = Path(..., ge=1),
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """删除用户（仅管理员）"""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    service = UserService(db)
    success = await service.delete_user(user_id)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}
