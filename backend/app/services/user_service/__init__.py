"""User service."""
from __future__ import annotations
from typing import Optional
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password, verify_password


class UserService:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username_or_email(db: AsyncSession, username_or_email: str) -> Optional[User]:
        result = await db.execute(
            select(User).where(or_(User.username == username_or_email, User.email == username_or_email))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate) -> User:
        existing = await db.execute(
            select(User).where(or_(User.username == user_data.username, User.email == user_data.email))
        )
        if existing.scalar_one_or_none():
            raise ValueError("用户名或邮箱已被使用")
        nickname = user_data.nickname or user_data.username
        user = User(
            username=user_data.username,
            email=user_data.email,
            nickname=nickname,
            hashed_password=hash_password(user_data.password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update(db: AsyncSession, user: User, user_data: UserUpdate) -> User:
        update_dict = user_data.model_dump(exclude_unset=True)
        if "phone" in update_dict:
            new_phone = update_dict["phone"]
            if new_phone != user.phone:
                user.phone_verified = False
                user.phone_verified_at = None
        for key, value in update_dict.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate(db: AsyncSession, username_or_email: str, password: str) -> Optional[User]:
        result = await db.execute(
            select(User).where(or_(User.username == username_or_email, User.email == username_or_email))
        )
        user = result.scalar_one_or_none()
        if user is None:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def is_username_taken(db: AsyncSession, username: str) -> bool:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def is_email_taken(db: AsyncSession, email: str) -> bool:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_user_list(db: AsyncSession, page: int = 1, page_size: int = 10, keyword: Optional[str] = None) -> tuple[list[User], int]:
        query = select(User)
        count_query = select(func.count()).select_from(User)
        if keyword:
            keyword_filter = or_(
                User.username.ilike(f"%{keyword}%"),
                User.email.ilike(f"%{keyword}%"),
                User.nickname.ilike(f"%{keyword}%"),
            )
            query = query.where(keyword_filter)
            count_query = count_query.where(keyword_filter)
        query = query.order_by(User.id.desc())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        users = list(result.scalars().all())
        return users, total


user_service = UserService()
