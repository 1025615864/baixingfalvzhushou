"""User service."""
from __future__ import annotations
import time
import enum
from typing import Optional
from dataclasses import dataclass, field


class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"
    PENDING = "pending"


@dataclass
class User:
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    last_login: Optional[float] = None
    metadata: dict = field(default_factory=dict)


class UserService:
    def __init__(self):
        self._users: dict[int, User] = {}
        self._next_id = 1

    async def create_user(self, username: str, email: Optional[str] = None, phone: Optional[str] = None) -> User:
        user_id = self._next_id
        self._next_id += 1
        user = User(id=user_id, username=username, email=email, phone=phone)
        self._users[user_id] = user
        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        user = self._users.get(user_id)
        if not user:
            return None
        for k, v in kwargs.items():
            if hasattr(user, k):
                setattr(user, k, v)
        return user

    async def delete_user(self, user_id: int) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False

    async def list_users(self, limit: int = 20, offset: int = 0) -> list[User]:
        users = list(self._users.values())
        return users[offset:offset + limit]

    async def ban_user(self, user_id: int) -> dict:
        user = self._users.get(user_id)
        if not user:
            return {"success": False, "error": "用户不存在"}
        user.status = UserStatus.BANNED
        return {"success": True}

    async def activate_user(self, user_id: int) -> dict:
        user = self._users.get(user_id)
        if not user:
            return {"success": False, "error": "用户不存在"}
        user.status = UserStatus.ACTIVE
        return {"success": True}


user_service = UserService()
