"""认证服务"""
from datetime import datetime, timedelta
from typing import Optional
import uuid

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.settings import get_settings
from ..models import User, LoginAudit
from ..events.kafka_client import get_publisher
from ..events.kafka_events import UserRegisteredEvent

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """认证服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    def _create_access_token(self, user: User) -> str:
        """创建访问令牌"""
        payload = {
            "sub": str(user.id),
            "role": user.role,
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes),
        }
        return jwt.encode(payload, settings.jwt_rsa_private_key, algorithm=settings.algorithm)

    def _create_refresh_token(self, user: User) -> str:
        """创建刷新令牌"""
        payload = {
            "sub": str(user.id),
            "role": user.role,
            "jti": str(uuid.uuid4()),
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
        }
        return jwt.encode(payload, settings.jwt_rsa_private_key, algorithm=settings.algorithm)

    async def login(self, phone: str, password: str) -> Optional[dict]:
        """用户登录"""
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()

        if not user or not self.verify_password(password, user.hashed_password):
            return None

        # 生成令牌
        access_token = self._create_access_token(user)
        refresh_token = self._create_refresh_token(user)

        # 记录登录
        audit = LoginAudit(
            user_id=user.id,
            event_type="login",
            success=True,
        )
        self.db.add(audit)
        await self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    async def register(self, phone: str, password: str) -> Optional[dict]:
        """用户注册"""
        # 检查手机号是否已存在
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        existing = result.scalar_one_or_none()

        if existing:
            return None

        # 创建用户
        user = User(
            phone=phone,
            hashed_password=self.hash_password(password),
            role="user",
            status="active",
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # 发布用户注册事件
        try:
            publisher = await get_publisher()
            if publisher:
                event = UserRegisteredEvent(
                    user_id=user.id,
                    phone=user.phone,
                    email=user.email or "",
                )
                await publisher.publish(event, key=str(user.id))
        except Exception:
            pass  # 忽略发布失败

        # 生成令牌
        access_token = self._create_access_token(user)
        refresh_token = self._create_refresh_token(user)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }
