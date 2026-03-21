"""用户路由"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from ..models import User

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str
    status: str
    is_verified: bool

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int


async def get_current_user_id(authorization: str = Header(None)) -> int:
    """从 Authorization header 获取当前用户ID"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = authorization[7:]
    
    if not token or token == "guest":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        return int(token.split("_")[1]) if "_" in token else int(token)
    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
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
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表"""
    query = select(User)
    
    if role:
        query = query.where(User.role == role)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size
    )


class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    request: UserUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """更新当前用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.email is not None:
        user.email = request.email
    if request.phone is not None:
        user.phone = request.phone
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)
