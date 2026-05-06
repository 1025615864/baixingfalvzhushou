"""认证服务"""
from datetime import datetime, timedelta
from typing import Optional
import uuid
import logging

from jose import jwt, ExpiredSignatureError, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config.settings import get_settings
from ..models import User, LoginAudit
from ..core.jwt_keys import jwt_key_manager
from .token_service import token_manager, login_rate_limiter
from .password_policy import password_policy

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)


def _get_signing_key():
    """获取签名的密钥"""
    if jwt_key_manager.is_using_rsa():
        return jwt_key_manager.private_key
    return settings.jwt_secret_key


def _get_verify_key():
    """获取验证的密钥"""
    if jwt_key_manager.is_using_rsa():
        return jwt_key_manager.public_key
    return settings.jwt_secret_key


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

    def _create_access_token(self, user: User, family: str = None) -> tuple[str, str]:
        """创建访问令牌

        Args:
            user: 用户对象
            family: Token家族ID（用于Refresh Token轮换追踪）

        Returns:
            (token, jti)
        """
        jti = str(uuid.uuid4())
        payload = {
            "sub": str(user.id),
            "uid": user.uid,
            "role": user.role,
            "jti": jti,
            "type": "access",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes),
        }
        if family:
            payload["family"] = family
        signing_key = _get_signing_key()
        return jwt.encode(payload, signing_key, algorithm=jwt_key_manager.algorithm), jti

    def _create_refresh_token(self, user: User, family: str = None) -> tuple[str, str]:
        """创建刷新令牌

        Args:
            user: 用户对象
            family: Token家族ID（用于Refresh Token轮换追踪）

        Returns:
            (token, jti)
        """
        jti = str(uuid.uuid4())
        if not family:
            family = str(uuid.uuid4())
        payload = {
            "sub": str(user.id),
            "uid": user.uid,
            "role": user.role,
            "jti": jti,
            "type": "refresh",
            "family": family,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
        }
        signing_key = _get_signing_key()
        return jwt.encode(payload, signing_key, algorithm=jwt_key_manager.algorithm), jti

    def _decode_token(self, token: str) -> Optional[dict]:
        """解码Token"""
        try:
            verify_key = _get_verify_key()
            payload = jwt.decode(
                token,
                verify_key,
                algorithms=[jwt_key_manager.algorithm]
            )
            return payload
        except ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            return None

    async def login(self, phone: str, password: str, ip_address: str = None) -> Optional[dict]:
        """用户登录"""
        # 检查是否被锁定
        is_locked, remaining = await login_rate_limiter.is_locked_out(phone)
        if is_locked:
            return {
                "error": "too_many_attempts",
                "message": f"登录尝试次数过多，请在 {remaining} 秒后重试",
                "retry_after": remaining,
            }

        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()

        if not user or not self.verify_password(password, user.hashed_password):
            if user:
                # 记录失败的登录尝试
                attempts, lockout = await login_rate_limiter.record_failed_attempt(phone)
                audit = LoginAudit(
                    user_id=user.id,
                    event_type="login_failed",
                    ip_address=ip_address,
                    success=False,
                    failure_reason="invalid_password",
                )
                self.db.add(audit)
                await self.db.commit()

                if lockout > 0:
                    return {
                        "error": "too_many_attempts",
                        "message": f"登录尝试次数过多，请在 {lockout} 秒后重试",
                        "retry_after": lockout,
                    }
            return None

        # 生成令牌
        access_token, access_jti = self._create_access_token(user)
        refresh_token, refresh_jti = self._create_refresh_token(user)

        # 清除失败尝试记录
        await login_rate_limiter.clear_failed_attempts(phone)

        # 记录登录
        audit = LoginAudit(
            user_id=user.id,
            event_type="login",
            ip_address=ip_address,
            success=True,
        )
        self.db.add(audit)
        await self.db.commit()

        # 发布登录事件
        try:
            from ..events.kafka_producer import publish_user_login
            await publish_user_login(str(user.id), ip_address)
        except Exception as e:
            logger.warning(f"Failed to publish login event: {e}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "access_jti": access_jti,
            "refresh_jti": refresh_jti,
            "uid": user.uid,
        }

    async def register(self, phone: str, password: str) -> Optional[dict]:
        """用户注册"""
        # 密码强度校验
        is_valid, error_msg = password_policy.validate(password)
        if not is_valid:
            logger.warning(f"Password validation failed: {error_msg}")
            return {"error": "weak_password", "message": error_msg}

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
            from ..events.kafka_producer import publish_user_registered
            await publish_user_registered(
                user_id=str(user.id),
                email=user.email or "",
                username=user.phone,
            )
        except Exception as e:
            logger.warning(f"Failed to publish registration event: {e}")

        # 生成令牌
        access_token, access_jti = self._create_access_token(user)
        refresh_token, refresh_jti = self._create_refresh_token(user)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "access_jti": access_jti,
            "refresh_jti": refresh_jti,
            "uid": user.uid,
        }

    async def refresh_access_token(self, refresh_token: str) -> Optional[dict]:
        """使用刷新令牌获取新的访问令牌（实现Refresh Token Rotation）

        - 检测Token重放攻击
        - 每次刷新生成新的refresh_token
        - 吊销整个Token家族如果检测到异常
        """
        payload = self._decode_token(refresh_token)
        if not payload:
            return None

        if payload.get("type") != "refresh":
            logger.warning("Token is not a refresh token")
            return None

        refresh_jti = payload.get("jti")
        if not refresh_jti:
            return None

        family = payload.get("family")

        if await token_manager.is_refresh_token_used(refresh_jti):
            logger.warning(f"Refresh token reuse detected! JTI: {refresh_jti}, Family: {family}")
            if family:
                await token_manager.revoke_token_family(family)
            try:
                from ..services.audit_service import AuditService
                from ..database import AsyncSessionLocal
                async with AsyncSessionLocal() as db:
                    audit_service = AuditService(db)
                    await audit_service.log(
                        user_id=int(payload.get("sub", 0)),
                        action="token_family_revoked",
                        resource="token",
                        resource_id=family,
                        status="danger",
                        details=f"Refresh token reuse detected, family {family} revoked",
                    )
            except Exception:
                pass
            return None

        if await token_manager.is_refresh_token_revoked(refresh_jti):
            logger.warning("Refresh token has been revoked")
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        result = await self.db.execute(
            select(User).where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()

        if not user or user.status != "active":
            return None

        await token_manager.mark_refresh_token_used(refresh_jti)

        access_token, access_jti = self._create_access_token(user, family)
        new_refresh_token, new_refresh_jti = self._create_refresh_token(user, family)

        remaining_seconds = settings.refresh_token_expire_days * 24 * 3600
        await token_manager.revoke_refresh_token(refresh_jti, remaining_seconds)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "access_jti": access_jti,
            "refresh_jti": new_refresh_jti,
            "uid": user.uid,
        }

    async def verify_token(self, token: str) -> Optional[dict]:
        """验证Token并返回用户信息"""
        payload = self._decode_token(token)
        if not payload:
            return None

        if payload.get("type") != "access":
            return None

        jti = payload.get("jti")
        if jti and await token_manager.is_access_token_revoked(jti):
            logger.info(f"Token has been revoked: {jti}")
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        result = await self.db.execute(
            select(User).where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        return {
            "user_id": user.id,
            "uid": user.uid,
            "role": user.role,
            "status": user.status,
        }

    async def get_user_by_uid(self, uid: str) -> Optional[dict]:
        """根据UID获取用户信息（不验证Token）"""
        result = await self.db.execute(
            select(User).where(User.uid == uid)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        return {
            "user_id": user.id,
            "uid": user.uid,
            "role": user.role,
            "status": user.status,
        }

    async def revoke_all_tokens(self, user_id: int) -> bool:
        """撤销用户所有令牌（用于密码修改等场景）"""
        return await token_manager.revoke_all_user_tokens(user_id)
