"""用户服务"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import User, UserProfile


class UserService:
    """用户服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """获取用户画像"""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user_profile(
        self,
        user_id: int,
        nickname: Optional[str] = None,
        avatar: Optional[str] = None,
        bio: Optional[str] = None,
        **kwargs
    ) -> Optional[UserProfile]:
        """更新用户画像"""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)

        if nickname is not None:
            profile.nickname = nickname
        if avatar is not None:
            profile.avatar = avatar
        if bio is not None:
            profile.bio = bio

        await self.db.commit()
        await self.db.refresh(profile)
        return profile
