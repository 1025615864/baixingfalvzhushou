"""JWT Token轮换机制模块

提供完整的Token轮换、黑名单管理和双Token策略支持。

功能特性:
    - Token刷新机制: 使用refresh_token换取新的access_token
    - Token黑名单: 使用Redis存储已撤销的token
    - 双Token策略: access_token(短期) + refresh_token(长期)
    - Token元数据追踪: 记录签发时间、过期时间、轮换次数
    - 轮换次数限制: 防止无限轮换攻击

使用示例:
    ```python
    from app.core.token_rotation import TokenRotationService
    
    # 创建token对
    tokens = await TokenRotationService.create_token_pair(
        user_id=123,
        user_email="user@example.com",
        user_role="user"
    )
    
    # 轮换token
    new_tokens = await TokenRotationService.rotate_tokens(
        refresh_token="old_refresh_token",
        user_id=123
    )
    
    # 撤销token
    await TokenRotationService.revoke_token("token_to_revoke")
    ```
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar, Literal, Optional
from dataclasses import dataclass, field

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete, update, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from ..config import get_settings
from ..database import Base
from ..services.redis_service import RedisService

settings = get_settings()
logger = logging.getLogger(__name__)


# ==================== Token配置常量 ====================

ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # access_token有效期: 15分钟
REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # refresh_token有效期: 7天
MAX_ROTATION_COUNT: int = 5  # 最大轮换次数，防止无限轮换
TOKEN_BLACKLIST_PREFIX: str = "token:revoked"  # Redis黑名单键前缀
TOKEN_FAMILY_PREFIX: str = "token:family"  # Token家族前缀
TOKEN_META_PREFIX: str = "token:meta"  # Token元数据前缀


# ==================== 数据模型 ====================

class RefreshTokenRecord(Base):
    """刷新Token数据库记录
    
    用于持久化存储refresh_token的元数据和状态，支持:
    - 追踪token家族（防止家族重放攻击）
    - 记录轮换次数
    - 标记撤销状态
    
    Attributes:
        id: 主键ID
        user_id: 用户ID
        token_jti: Token唯一标识符
        token_family: Token家族标识（同一登录会话的token族）
        issued_at: 签发时间
        expires_at: 过期时间
        rotated_at: 上次轮换时间
        rotation_count: 轮换次数
        is_revoked: 是否已撤销
        revoked_at: 撤销时间
        revoked_reason: 撤销原因
        device_info: 设备信息（可选）
        ip_address: IP地址（可选）
    """
    
    __tablename__ = "refresh_tokens"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(index=True, nullable=False)
    token_jti: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    token_family: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    rotated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rotation_count: Mapped[int] = mapped_column(default=0)
    is_revoked: Mapped[bool] = mapped_column(default=False, index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_reason: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    device_info: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True  # 支持IPv6
    )
    
    def __repr__(self) -> str:
        return f"<RefreshTokenRecord(jti={self.token_jti}, user={self.user_id})>"


@dataclass
class TokenMetadata:
    """Token元数据
    
    存储在Redis中的token附加信息。
    
    Attributes:
        jti: Token唯一标识符
        sub: 用户ID
        type: Token类型 (access/refresh)
        issued_at: 签发时间戳
        expires_at: 过期时间戳
        family: Token家族
        rotation_count: 轮换次数
    """
    
    jti: str
    sub: int
    type: Literal["access", "refresh"]
    issued_at: int
    expires_at: int
    family: str
    rotation_count: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "jti": self.jti,
            "sub": self.sub,
            "type": self.type,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "family": self.family,
            "rotation_count": self.rotation_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenMetadata":
        """从字典创建实例"""
        return cls(
            jti=data["jti"],
            sub=data["sub"],
            type=data["type"],
            issued_at=data["issued_at"],
            expires_at=data["expires_at"],
            family=data["family"],
            rotation_count=data.get("rotation_count", 0),
        )


@dataclass
class TokenPair:
    """Token对（access_token + refresh_token）"""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = field(default_factory=lambda: ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    def to_response(self) -> dict[str, Any]:
        """转换为API响应格式"""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
        }


# ==================== 核心服务类 ====================

class TokenRotationService:
    """Token轮换服务
    
    提供完整的token生命周期管理，包括创建、验证、轮换和撤销。
    
    安全特性:
        - Token家族机制: 防止家族重放攻击
        - 轮换次数限制: 防止无限轮换
        - 黑名单机制: 支持主动撤销
        - 双Token策略: 短期access_token + 长期refresh_token
    """
    
    _redis: ClassVar[Optional[RedisService]] = None
    
    @classmethod
    def _get_redis(cls) -> Optional[RedisService]:
        """获取Redis服务实例（延迟初始化）"""
        if cls._redis is None:
            cls._redis = RedisService()
        return cls._redis
    
    @classmethod
    def _get_jwt_key_and_algorithm(cls) -> tuple[str, str]:
        """获取JWT密钥和算法
        
        Returns:
            tuple: (密钥, 算法)
        """
        algorithm = settings.algorithm
        
        if algorithm == "RS256":
            if not settings.jwt_rsa_private_key:
                raise ValueError("JWT_RSA_PRIVATE_KEY must be set for RS256 algorithm")
            return settings.jwt_rsa_private_key, algorithm
        else:
            if not settings.secret_key:
                raise ValueError("SECRET_KEY must be set for HS256 algorithm")
            return settings.secret_key, algorithm
    
    @classmethod
    def _get_public_key(cls) -> str:
        """获取JWT公钥（用于验证）"""
        algorithm = settings.algorithm
        
        if algorithm == "RS256":
            if not settings.jwt_rsa_public_key:
                raise ValueError("JWT_RSA_PUBLIC_KEY must be set for RS256 algorithm")
            return settings.jwt_rsa_public_key
        else:
            if not settings.secret_key:
                raise ValueError("SECRET_KEY must be set for HS256 algorithm")
            return settings.secret_key
    
    @classmethod
    def _generate_jti(cls) -> str:
        """生成Token唯一标识符"""
        return str(uuid.uuid4())
    
    @classmethod
    def _generate_family(cls) -> str:
        """生成Token家族标识"""
        return f"fam_{uuid.uuid4().hex[:16]}"
    
    @classmethod
    def _calculate_expiry(cls, token_type: Literal["access", "refresh"]) -> datetime:
        """计算Token过期时间
        
        Args:
            token_type: Token类型
            
        Returns:
            过期时间
        """
        now = datetime.now(timezone.utc)
        if token_type == "access":
            return now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            return now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    @classmethod
    def _create_token(
        cls,
        user_id: int,
        user_email: str,
        user_role: str,
        token_type: Literal["access", "refresh"],
        family: str,
        jti: str,
        rotation_count: int = 0,
    ) -> tuple[str, datetime]:
        """创建JWT Token
        
        Args:
            user_id: 用户ID
            user_email: 用户邮箱
            user_role: 用户角色
            token_type: Token类型
            family: Token家族
            jti: Token唯一标识
            rotation_count: 轮换次数
            
        Returns:
            tuple: (token字符串, 过期时间)
        """
        expire = cls._calculate_expiry(token_type)
        
        payload: dict[str, Any] = {
            "sub": user_id,
            "email": user_email,
            "role": user_role,
            "jti": jti,
            "type": token_type,
            "family": family,
            "rot": rotation_count,  # rotation_count缩写
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int(expire.timestamp()),
        }
        
        key, algorithm = cls._get_jwt_key_and_algorithm()
        token = jwt.encode(payload, key, algorithm=algorithm)
        
        return token, expire
    
    @classmethod
    async def create_token_pair(
        cls,
        user_id: int,
        user_email: str,
        user_role: str = "user",
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> TokenPair:
        """创建新的Token对（登录时使用）
        
        Args:
            user_id: 用户ID
            user_email: 用户邮箱
            user_role: 用户角色
            device_info: 设备信息
            ip_address: IP地址
            db: 数据库会话（可选，用于持久化refresh_token）
            
        Returns:
            TokenPair对象
        """
        family = cls._generate_family()
        
        # 创建access_token
        access_jti = cls._generate_jti()
        access_token, _ = cls._create_token(
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            token_type="access",
            family=family,
            jti=access_jti,
        )
        
        # 创建refresh_token
        refresh_jti = cls._generate_jti()
        refresh_token, refresh_expire = cls._create_token(
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            token_type="refresh",
            family=family,
            jti=refresh_jti,
            rotation_count=0,
        )
        
        # 存储token元数据到Redis
        now = int(datetime.now(timezone.utc).timestamp())
        redis = cls._get_redis()
        if redis:
            try:
                # 存储access_token元数据（短期）
                access_meta = TokenMetadata(
                    jti=access_jti,
                    sub=user_id,
                    type="access",
                    issued_at=now,
                    expires_at=int(
                        (datetime.now(timezone.utc) + 
                         timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
                    ),
                    family=family,
                    rotation_count=0,
                )
                await cls._store_token_metadata(redis, access_meta)
                
                # 存储refresh_token元数据（长期）
                refresh_meta = TokenMetadata(
                    jti=refresh_jti,
                    sub=user_id,
                    type="refresh",
                    issued_at=now,
                    expires_at=int(refresh_expire.timestamp()),
                    family=family,
                    rotation_count=0,
                )
                await cls._store_token_metadata(redis, refresh_meta)
                
                # 记录token家族
                await redis.set(
                    f"{TOKEN_FAMILY_PREFIX}:{family}",
                    str(user_id),
                    expire_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
                )
            except Exception as e:
                logger.warning(f"Failed to store token metadata: {e}")
        
        # 持久化refresh_token到数据库
        if db:
            try:
                record = RefreshTokenRecord(
                    user_id=user_id,
                    token_jti=refresh_jti,
                    token_family=family,
                    issued_at=datetime.now(timezone.utc),
                    expires_at=refresh_expire,
                    rotation_count=0,
                    is_revoked=False,
                    device_info=device_info,
                    ip_address=ip_address,
                )
                db.add(record)
                await db.commit()
                logger.debug(f"Refresh token persisted: {refresh_jti}")
            except Exception as e:
                logger.warning(f"Failed to persist refresh token: {e}")
                await db.rollback()
        
        logger.info(f"Token pair created for user {user_id}, family {family}")
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    
    @classmethod
    async def _store_token_metadata(
        cls,
        redis: RedisService,
        meta: TokenMetadata,
    ) -> None:
        """存储token元数据到Redis
        
        Args:
            redis: Redis服务实例
            meta: Token元数据
        """
        ttl = meta.expires_at - int(datetime.now(timezone.utc).timestamp())
        if ttl > 0:
            await redis.set_json(
                f"{TOKEN_META_PREFIX}:{meta.jti}",
                meta.to_dict(),
                expire_seconds=ttl,
            )
    
    @classmethod
    async def decode_token(cls, token: str) -> Optional[dict[str, Any]]:
        """解码JWT Token
        
        Args:
            token: JWT字符串
            
        Returns:
            解码后的payload，失败返回None
        """
        try:
            key = cls._get_public_key()
            algorithm = settings.algorithm
            payload = jwt.decode(
                token,
                key,
                algorithms=[algorithm],
                options={"verify_aud": False},
            )
            return payload
        except JWTError as e:
            logger.debug(f"Token decode failed: {e}")
            return None
    
    @classmethod
    async def verify_token(
        cls,
        token: str,
        expected_type: Optional[Literal["access", "refresh"]] = None,
    ) -> Optional[dict[str, Any]]:
        """验证Token（包括黑名单检查）
        
        Args:
            token: JWT字符串
            expected_type: 期望的token类型（可选）
            
        Returns:
            验证通过的payload，失败返回None
        """
        payload = await cls.decode_token(token)
        if not payload:
            return None
        
        # 检查token类型
        token_type = payload.get("type")
        if expected_type and token_type != expected_type:
            logger.debug(f"Token type mismatch: {token_type} != {expected_type}")
            return None
        
        # 检查黑名单
        jti = payload.get("jti")
        if jti and await cls.is_token_revoked(str(jti)):
            logger.warning(f"Token is revoked: {jti}")
            return None
        
        return payload
    
    @classmethod
    async def is_token_revoked(cls, jti: str) -> bool:
        """检查token是否已被撤销
        
        Args:
            jti: Token唯一标识符
            
        Returns:
            True表示已撤销
        """
        redis = cls._get_redis()
        if not redis or not redis.is_connected:
            return False
        
        try:
            revoked = await redis.get(f"{TOKEN_BLACKLIST_PREFIX}:{jti}")
            return revoked is not None
        except Exception as e:
            logger.warning(f"Failed to check token revocation: {e}")
            return False
    
    @classmethod
    async def revoke_token(
        cls,
        token: Optional[str] = None,
        jti: Optional[str] = None,
        reason: str = "manual",
        expire_seconds: Optional[int] = None,
        db: Optional[AsyncSession] = None,
    ) -> bool:
        """撤销Token
        
        Args:
            token: JWT字符串（与jti二选一）
            jti: Token唯一标识（与token二选一）
            reason: 撤销原因
            expire_seconds: 黑名单过期时间（默认与token过期时间一致）
            db: 数据库会话（用于更新refresh_token记录）
            
        Returns:
            是否成功撤销
        """
        if not token and not jti:
            logger.error("Either token or jti must be provided")
            return False
        
        # 获取jti和过期时间
        if token:
            payload = await cls.decode_token(token)
            if not payload:
                logger.warning("Cannot revoke invalid token")
                return False
            
            jti = str(payload.get("jti", ""))
            exp = payload.get("exp")
            if not jti:
                logger.warning("Token has no jti")
                return False
            
            # 计算剩余TTL
            if not expire_seconds and exp:
                remaining = int(exp) - int(datetime.now(timezone.utc).timestamp())
                expire_seconds = max(remaining, 60)  # 至少保留1分钟
        else:
            expire_seconds = expire_seconds or (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600)
        
        # 添加到Redis黑名单
        redis = cls._get_redis()
        if redis and redis.is_connected:
            try:
                await redis.set(
                    f"{TOKEN_BLACKLIST_PREFIX}:{jti}",
                    reason,
                    expire_seconds=expire_seconds,
                )
                logger.info(f"Token revoked: {jti}, reason: {reason}")
            except Exception as e:
                logger.error(f"Failed to revoke token in Redis: {e}")
                return False
        
        # 更新数据库记录（如果是refresh_token）
        if db and token:
            payload = await cls.decode_token(token)
            if payload and payload.get("type") == "refresh":
                try:
                    from sqlalchemy import update
                    stmt = (
                        update(RefreshTokenRecord)
                        .where(RefreshTokenRecord.token_jti == jti)
                        .values(
                            is_revoked=True,
                            revoked_at=datetime.now(timezone.utc),
                            revoked_reason=reason,
                        )
                    )
                    await db.execute(stmt)
                    await db.commit()
                except Exception as e:
                    logger.warning(f"Failed to update refresh token record: {e}")
                    await db.rollback()
        
        return True
    
    @classmethod
    async def revoke_family(
        cls,
        family: str,
        reason: str = "family_compromised",
        db: Optional[AsyncSession] = None,
    ) -> int:
        """撤销整个Token家族
        
        用于检测重放攻击时撤销整个token家族的所有token。
        
        Args:
            family: Token家族标识
            reason: 撤销原因
            db: 数据库会话
            
        Returns:
            撤销的token数量
        """
        # 从数据库中查找该家族的所有token
        revoked_count = 0
        if db:
            try:
                from sqlalchemy import update
                stmt = (
                    update(RefreshTokenRecord)
                    .where(
                        and_(
                            RefreshTokenRecord.token_family == family,
                            RefreshTokenRecord.is_revoked == False,
                        )
                    )
                    .values(
                        is_revoked=True,
                        revoked_at=datetime.now(timezone.utc),
                        revoked_reason=reason,
                    )
                )
                await db.execute(stmt)
                await db.commit()
                revoked_count = 1  # Simplified count
            except Exception as e:
                logger.error(f"Failed to revoke token family in DB: {e}")
                await db.rollback()
        
        # 将家族标记为撤销
        redis = cls._get_redis()
        if redis and redis.is_connected:
            try:
                await redis.set(
                    f"{TOKEN_FAMILY_PREFIX}:{family}:revoked",
                    reason,
                    expire_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
                )
            except Exception as e:
                logger.error(f"Failed to mark family as revoked: {e}")
        
        logger.warning(f"Token family revoked: {family}, count: {revoked_count}")
        return revoked_count
    
    @classmethod
    async def rotate_tokens(
        cls,
        refresh_token: str,
        db: Optional[AsyncSession] = None,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[TokenPair]:
        """Token轮换 - 使用refresh_token换取新的token对
        
        实现机制:
        1. 验证refresh token的有效性
        2. 检查token是否已被撤销（防止重放攻击）
        3. 检查轮换次数限制
        4. 验证token家族状态
        5. 撤销旧的refresh_token
        6. 生成新的token对
        
        Args:
            refresh_token: 当前refresh_token
            db: 数据库会话
            device_info: 新设备信息
            ip_address: 新IP地址
            
        Returns:
            新的TokenPair，失败返回None
        """
        # 1. 验证refresh token
        payload = await cls.verify_token(refresh_token, expected_type="refresh")
        if not payload:
            logger.warning("Token rotation failed: invalid refresh token")
            return None
        
        user_id = int(payload.get("sub", 0))
        email = str(payload.get("email", ""))
        role = str(payload.get("role", "user"))
        jti = str(payload.get("jti", ""))
        family = str(payload.get("family", ""))
        rotation_count = int(payload.get("rot", 0))
        
        if not user_id or not jti or not family:
            logger.warning("Token rotation failed: missing required claims")
            return None
        
        # 2. 检查轮换次数限制
        if rotation_count >= MAX_ROTATION_COUNT:
            logger.warning(
                f"Token rotation limit exceeded: user={user_id}, count={rotation_count}"
            )
            # 撤销整个家族（可能遭受攻击）
            await cls.revoke_family(family, "rotation_limit_exceeded", db)
            return None
        
        # 3. 检查家族是否已被撤销（检测重放攻击）
        redis = cls._get_redis()
        if redis and redis.is_connected:
            family_revoked = await redis.get(
                f"{TOKEN_FAMILY_PREFIX}:{family}:revoked"
            )
            if family_revoked:
                logger.warning(
                    f"Token rotation failed: family already revoked (replay attack?), "
                    f"user={user_id}, family={family}"
                )
                return None
        
        # 4. 从数据库验证token状态
        if db:
            try:
                result = await db.execute(
                    select(RefreshTokenRecord).where(
                        RefreshTokenRecord.token_jti == jti
                    )
                )
                record = result.scalar_one_or_none()
                
                if not record:
                    logger.warning(f"Refresh token not found in DB: {jti}")
                    return None
                
                if record.is_revoked:
                    logger.warning(
                        f"Token rotation failed: token already revoked, "
                        f"user={user_id}, jti={jti}"
                    )
                    # 可能遭受重放攻击，撤销整个家族
                    await cls.revoke_family(family, "replay_attack_detected", db)
                    return None
                
                # 检查数据库中的轮换次数一致性
                if record.rotation_count != rotation_count:
                    logger.warning(
                        f"Token rotation count mismatch: JWT={rotation_count}, "
                        f"DB={record.rotation_count}, possible tampering"
                    )
                    await cls.revoke_family(family, "rotation_count_mismatch", db)
                    return None
                
            except Exception as e:
                logger.error(f"Failed to verify refresh token in DB: {e}")
                return None
        
        # 5. 撤销旧的refresh_token
        await cls.revoke_token(
            token=refresh_token,
            reason="rotated",
            db=db,
        )
        
        # 6. 创建新的token对（保持同一family）
        new_rotation_count = rotation_count + 1
        
        new_access_jti = cls._generate_jti()
        new_refresh_jti = cls._generate_jti()
        now = datetime.now(timezone.utc)
        
        new_access_token, _ = cls._create_token(
            user_id=user_id,
            user_email=email,
            user_role=role,
            token_type="access",
            family=family,
            jti=new_access_jti,
            rotation_count=new_rotation_count,
        )
        
        new_refresh_token, new_refresh_expire = cls._create_token(
            user_id=user_id,
            user_email=email,
            user_role=role,
            token_type="refresh",
            family=family,
            jti=new_refresh_jti,
            rotation_count=new_rotation_count,
        )
        
        # 7. 存储新token元数据
        if redis and redis.is_connected:
            try:
                now_ts = int(now.timestamp())
                
                # Access token元数据
                access_meta = TokenMetadata(
                    jti=new_access_jti,
                    sub=user_id,
                    type="access",
                    issued_at=now_ts,
                    expires_at=int(
                        (now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
                    ),
                    family=family,
                    rotation_count=new_rotation_count,
                )
                await cls._store_token_metadata(redis, access_meta)
                
                # Refresh token元数据
                refresh_meta = TokenMetadata(
                    jti=new_refresh_jti,
                    sub=user_id,
                    type="refresh",
                    issued_at=now_ts,
                    expires_at=int(new_refresh_expire.timestamp()),
                    family=family,
                    rotation_count=new_rotation_count,
                )
                await cls._store_token_metadata(redis, refresh_meta)
                
            except Exception as e:
                logger.warning(f"Failed to store new token metadata: {e}")
        
        # 8. 持久化新的refresh_token到数据库
        if db:
            try:
                # 更新旧记录
                await db.execute(
                    update(RefreshTokenRecord)
                    .where(RefreshTokenRecord.token_jti == jti)
                    .values(
                        rotated_at=now,
                        rotation_count=new_rotation_count,
                    )
                )
                
                # 创建新记录
                new_record = RefreshTokenRecord(
                    user_id=user_id,
                    token_jti=new_refresh_jti,
                    token_family=family,
                    issued_at=now,
                    expires_at=new_refresh_expire,
                    rotation_count=new_rotation_count,
                    is_revoked=False,
                    device_info=device_info,
                    ip_address=ip_address,
                )
                db.add(new_record)
                await db.commit()
                
            except Exception as e:
                logger.error(f"Failed to persist rotated token: {e}")
                await db.rollback()
                return None
        
        logger.info(
            f"Token rotated successfully: user={user_id}, "
            f"family={family}, count={new_rotation_count}"
        )
        
        return TokenPair(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )
    
    @classmethod
    async def cleanup_expired_tokens(cls, db: AsyncSession) -> int:
        """清理过期的token记录
        
        定期清理数据库中已过期的refresh_token记录。
        
        Args:
            db: 数据库会话
            
        Returns:
            清理的记录数量
        """
        try:
            from sqlalchemy import delete
            stmt = (
                delete(RefreshTokenRecord)
                .where(
                    or_(
                        RefreshTokenRecord.expires_at < datetime.now(timezone.utc),
                        and_(
                            RefreshTokenRecord.is_revoked == True,
                            RefreshTokenRecord.revoked_at < (
                                datetime.now(timezone.utc) - timedelta(days=7)
                            ),
                        ),
                    )
                )
            )
            await db.execute(stmt)
            await db.commit()
            
            logger.info("Cleaned up expired token records")
            return 0  # Simplified return
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            await db.rollback()
            return 0
    
    @classmethod
    async def get_user_active_tokens(
        cls,
        user_id: int,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """获取用户的活跃token列表
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            活跃token记录列表
        """
        try:
            result = await db.execute(
                select(RefreshTokenRecord).where(
                    and_(
                        RefreshTokenRecord.user_id == user_id,
                        RefreshTokenRecord.is_revoked == False,
                        RefreshTokenRecord.expires_at > datetime.now(timezone.utc),
                    )
                )
            )
            records = result.scalars().all()
            
            return [
                {
                    "jti": r.token_jti,
                    "family": r.token_family,
                    "issued_at": r.issued_at.isoformat(),
                    "expires_at": r.expires_at.isoformat(),
                    "rotation_count": r.rotation_count,
                    "device_info": r.device_info,
                    "ip_address": r.ip_address,
                }
                for r in records
            ]
        except Exception as e:
            logger.error(f"Failed to get user active tokens: {e}")
            return []
    
    @classmethod
    async def revoke_all_user_tokens(
        cls,
        user_id: int,
        reason: str,
        db: AsyncSession,
    ) -> int:
        """撤销用户的所有token
        
        用于用户登出、密码修改、账号异常等场景。
        
        Args:
            user_id: 用户ID
            reason: 撤销原因
            db: 数据库会话
            
        Returns:
            撤销的token数量
        """
        try:
            # 获取所有活跃token
            result = await db.execute(
                select(RefreshTokenRecord).where(
                    and_(
                        RefreshTokenRecord.user_id == user_id,
                        RefreshTokenRecord.is_revoked == False,
                    )
                )
            )
            records = result.scalars().all()
            
            revoked_count = 0
            for record in records:
                # 撤销家族
                family_revoked = await cls.revoke_family(
                    record.token_family, reason, db
                )
                revoked_count += family_revoked
            
            logger.info(f"Revoked all tokens for user {user_id}: {revoked_count}")
            return revoked_count
            
        except Exception as e:
            logger.error(f"Failed to revoke all user tokens: {e}")
            await db.rollback()
            return 0


# ==================== 便捷函数 ====================

async def create_token_pair(
    user_id: int,
    user_email: str,
    user_role: str = "user",
    **kwargs,
) -> TokenPair:
    """便捷函数：创建token对"""
    return await TokenRotationService.create_token_pair(
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        **kwargs,
    )


async def rotate_tokens(refresh_token: str, **kwargs) -> Optional[TokenPair]:
    """便捷函数：轮换token"""
    return await TokenRotationService.rotate_tokens(refresh_token, **kwargs)


async def revoke_token(token: Optional[str] = None, **kwargs) -> bool:
    """便捷函数：撤销token"""
    return await TokenRotationService.revoke_token(token=token, **kwargs)


async def verify_token(
    token: str,
    expected_type: Optional[Literal["access", "refresh"]] = None,
) -> Optional[dict[str, Any]]:
    """便捷函数：验证token"""
    return await TokenRotationService.verify_token(token, expected_type)


# ==================== 异常类 ====================

class TokenRotationError(Exception):
    """Token轮换异常基类"""
    pass


class TokenRevokedError(TokenRotationError):
    """Token已被撤销异常"""
    pass


class RotationLimitExceededError(TokenRotationError):
    """轮换次数超限异常"""
    pass


class ReplayAttackDetectedError(TokenRotationError):
    """检测到重放攻击异常"""
    pass