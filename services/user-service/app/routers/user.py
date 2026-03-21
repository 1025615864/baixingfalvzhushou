"""用户路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import AsyncSessionLocal
from ..models import User
from ..services.user_service import UserService

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    phone: str
    email: Optional[str] = None
    role: str
    status: str
    is_verified: bool

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: int = 1):
    """获取当前用户信息（模拟）"""
    return UserResponse(
        id=user_id,
        phone="138****1234",
        email="user@example.com",
        role="user",
        status="active",
        is_verified=True
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(lambda: AsyncSessionLocal())):
    """获取用户详情"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(user)


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    role: Optional[str] = None,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取用户列表"""
    query = select(User)

    if role:
        query = query.where(User.role == role)

    # 获取总数
    total_result = await db.execute(select(User.id))
    total = len(total_result.scalars().all())

    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size
    )
