"""JWT 密钥管理 - 支持安全轮换

提供 JWT 密钥的安全管理、自动轮换和向后兼容。
支持：
- 多密钥同时有效（旧密钥过期前）
- 自动轮换机制
- 密钥版本管理
- 密钥持久化
"""
import os
import hmac
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

Base = DeclarativeBase()


class JWTKey(Base):
    """JWT 密钥表"""
    __tablename__ = "jwt_keys"

    id = Column(Integer, primary_key=True)
    version = Column(Integer, unique=True, nullable=False)
    secret = Column(String(256), nullable=False)
    algorithm = Column(String(20), default="HS256")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    rotated_at = Column(DateTime, nullable=True)


class JWTKeyManager:
    """JWT 密钥管理器"""

    def __init__(self, db_session_factory, rotation_days: int = 90, grace_period_days: int = 7):
        self.db_session_factory = db_session_factory
        self.rotation_days = rotation_days
        self.grace_period_days = grace_period_days
        self._cache: dict[int, str] = {}
        self._active_version: Optional[int] = None

    def _get_or_create_key(self, db) -> tuple[int, str]:
        """获取或创建活跃密钥"""
        active_key = db.query(JWTKey).filter(JWTKey.is_active == True).order_by(JWTKey.version.desc()).first()

        if active_key:
            now = datetime.now(timezone.utc)
            if active_key.expires_at and active_key.expires_at < now:
                return self._rotate_key(db, active_key)
            return active_key.version, active_key.secret

        return self._create_initial_key(db)

    def _create_initial_key(self, db) -> tuple[int, str]:
        """创建初始密钥"""
        secret = secrets.token_hex(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.rotation_days)

        key = JWTKey(
            version=1,
            secret=secret,
            algorithm="HS256",
            is_active=True,
            expires_at=expires_at,
        )
        db.add(key)
        db.commit()
        db.refresh(key)

        logger.info(f"Initial JWT key created: version {key.version}")
        return key.version, key.secret

    def _rotate_key(self, db, old_key: JWTKey) -> tuple[int, str]:
        """轮换密钥"""
        new_version = old_key.version + 1
        secret = secrets.token_hex(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.rotation_days)

        new_key = JWTKey(
            version=new_version,
            secret=secret,
            algorithm="HS256",
            is_active=True,
            expires_at=expires_at,
        )

        old_key.is_active = False
        old_key.rotated_at = datetime.now(timezone.utc)

        db.add(new_key)
        db.commit()
        db.refresh(new_key)

        self._active_version = new_version
        self._cache = {}

        logger.info(f"JWT key rotated: {old_key.version} -> {new_version}")
        return new_key.version, new_key.secret

    def get_active_key(self) -> tuple[int, str]:
        """获取当前活跃密钥"""
        if self._active_version and self._active_version in self._cache:
            return self._active_version, self._cache[self._active_version]

        db = self.db_session_factory()
        try:
            version, secret = self._get_or_create_key(db)
            self._active_version = version
            self._cache[version] = secret
            return version, secret
        finally:
            db.close()

    def create_token(self, payload: dict, expires_minutes: int = 60) -> str:
        """创建 JWT token"""
        version, secret = self.get_active_key()

        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        payload["exp"] = int(expire.timestamp())
        payload["kid"] = version

        token = jwt.encode(payload, secret, algorithm="HS256")
        return token

    def decode_token(self, token: str) -> Optional[dict]:
        """解码 JWT token（支持多密钥）"""
        db = self.db_session_factory()
        try:
            keys = db.query(JWTKey).filter(JWTKey.is_active == True).all()
            keys += db.query(JWTKey).filter(
                JWTKey.is_active == False,
                JWTKey.rotated_at > datetime.now(timezone.utc) - timedelta(days=self.grace_period_days),
            ).all()

            for key in keys:
                try:
                    payload = jwt.decode(token, key.secret, algorithms=[key.algorithm])
                    return payload
                except JWTError:
                    continue

            logger.warning("JWT token decode failed: no valid key found")
            return None
        finally:
            db.close()

    def force_rotate(self) -> tuple[int, str]:
        """强制轮换密钥"""
        db = self.db_session_factory()
        try:
            old_key = db.query(JWTKey).filter(JWTKey.is_active == True).first()
            if not old_key:
                return self._create_initial_key(db)
            return self._rotate_key(db, old_key)
        finally:
            db.close()

    def cleanup_expired_keys(self) -> int:
        """清理过期密钥"""
        db = self.db_session_factory()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=self.grace_period_days + 30)
            deleted = db.query(JWTKey).filter(
                JWTKey.is_active == False,
                JWTKey.rotated_at < cutoff,
            ).delete(synchronize_session=False)
            db.commit()
            if deleted:
                logger.info(f"Cleaned up {deleted} expired JWT keys")
            return deleted
        finally:
            db.close()

    def get_key_stats(self) -> dict:
        """获取密钥统计"""
        db = self.db_session_factory()
        try:
            total = db.query(JWTKey).count()
            active = db.query(JWTKey).filter(JWTKey.is_active == True).count()
            latest = db.query(JWTKey).order_by(JWTKey.version.desc()).first()

            return {
                "total_keys": total,
                "active_keys": active,
                "current_version": latest.version if latest else None,
                "next_rotation": latest.expires_at.isoformat() if latest and latest.expires_at else None,
            }
        finally:
            db.close()
