"""用户服务"""
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import User, UserProfile

logger = logging.getLogger(__name__)


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

    async def get_user_by_uid(self, uid: str) -> Optional[User]:
        """根据UID获取用户"""
        result = await self.db.execute(
            select(User).where(User.uid == uid)
        )
        return result.scalar_one_or_none()

    async def get_user_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_all_users(self, skip: int = 0, limit: int = 20) -> list[User]:
        """获取所有用户（分页）"""
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        role: Optional[str] = None,
        **kwargs
    ) -> Optional[User]:
        """更新用户（仅限User表核心字段，nickname/avatar在UserProfile中管理）"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        old_role = user.role
        changed_fields = []

        if username is not None:
            user.username = username
            changed_fields.append("username")
        if email is not None:
            user.email = email
            changed_fields.append("email")
        if phone is not None:
            user.phone = phone
            changed_fields.append("phone")
        if role is not None:
            user.role = role
            changed_fields.append("role")

        await self.db.commit()
        await self.db.refresh(user)

        try:
            from ..events.kafka_producer import publish_role_changed
            if role != old_role:
                await publish_role_changed(
                    user_id=str(user_id),
                    old_role=old_role,
                    new_role=role,
                )
        except Exception as e:
            logger.warning(f"Failed to publish user update event: {e}")

        return user

    async def delete_user(self, user_id: int, deleted_by: Optional[str] = None) -> bool:
        """软删除用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.deleted_at = datetime.utcnow()
        user.is_active = False
        await self.db.commit()

        try:
            from ..events.kafka_producer import publish_account_deleted
            await publish_account_deleted(
                user_id=str(user_id),
                deleted_by=deleted_by,
            )
        except Exception as e:
            logger.warning(f"Failed to publish account deleted event: {e}")

        return True

    async def ban_user(self, user_id: int, reason: Optional[str] = None, banned_by: Optional[str] = None) -> bool:
        """封禁用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.status = "banned"
        user.is_active = False
        await self.db.commit()

        try:
            from ..events.kafka_producer import publish_account_banned
            await publish_account_banned(
                user_id=str(user_id),
                reason=reason,
                banned_by=banned_by,
            )
        except Exception as e:
            logger.warning(f"Failed to publish account banned event: {e}")

        return True

    async def verify_lawyer(
        self,
        user_id: int,
        is_verified: bool = True,
        firm_name: Optional[str] = None,
    ) -> bool:
        """律师认证"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.role = "lawyer" if is_verified else "user"
        await self.db.commit()

        try:
            from ..events.kafka_producer import publish_lawyer_verified
            await publish_lawyer_verified(
                user_id=str(user_id),
                is_verified=is_verified,
                firm_name=firm_name,
            )
        except Exception as e:
            logger.warning(f"Failed to publish lawyer verified event: {e}")

        return True

    async def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """获取用户画像"""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user_profile(
        self,
        user_id: int,
        nickname: Optional[str] = None,
        avatar: Optional[str] = None,
        bio: Optional[str] = None,
        gender: Optional[str] = None,
        birthday: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
    ) -> UserProfile:
        """创建用户画像"""
        profile = UserProfile(
            user_id=user_id,
            nickname=nickname,
            avatar=avatar,
            bio=bio,
            gender=gender,
            province=province,
            city=city,
        )
        if birthday:
            try:
                profile.birthday = datetime.fromisoformat(birthday)
            except ValueError:
                pass

        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update_user_profile(
        self,
        user_id: int,
        nickname: Optional[str] = None,
        avatar: Optional[str] = None,
        bio: Optional[str] = None,
        gender: Optional[str] = None,
        birthday: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Optional[UserProfile]:
        """更新用户画像"""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)

        old_nickname = profile.nickname
        old_avatar = profile.avatar
        changed_fields = []

        if nickname is not None:
            profile.nickname = nickname
            changed_fields.append("nickname")
        if avatar is not None:
            profile.avatar = avatar
            changed_fields.append("avatar")
        if bio is not None:
            profile.bio = bio
            changed_fields.append("bio")
        if gender is not None:
            profile.gender = gender
            changed_fields.append("gender")
        if birthday is not None:
            try:
                profile.birthday = datetime.fromisoformat(birthday)
                changed_fields.append("birthday")
            except ValueError:
                pass
        if province is not None:
            profile.province = province
            changed_fields.append("province")
        if city is not None:
            profile.city = city
            changed_fields.append("city")

        await self.db.commit()
        await self.db.refresh(profile)

        try:
            from ..events.kafka_producer import publish_profile_updated
            if nickname != old_nickname or avatar != old_avatar:
                await publish_profile_updated(
                    user_id=str(user_id),
                    nickname=profile.nickname,
                    avatar=profile.avatar,
                    changed_fields=changed_fields,
                )
        except Exception as e:
            logger.warning(f"Failed to publish profile update event: {e}")

        return profile

    async def delete_user_profile(self, user_id: int) -> bool:
        """删除用户画像"""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return False

        await self.db.delete(profile)
        await self.db.commit()
        return True
