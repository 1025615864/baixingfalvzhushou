"""Secret encryption helpers with key rotation support."""

from __future__ import annotations

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from ..config import get_settings


_ENC_PREFIX = "enc:"


# 密钥版本管理
class KeyManager:
    """密钥版本管理器"""
    
    def __init__(self):
        self._keys: dict[int, Fernet] = {}
        self._current_version = 1
    
    def add_key(self, version: int, key: str) -> None:
        """添加密钥版本"""
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        fernet_key = base64.urlsafe_b64encode(digest)
        self._keys[version] = Fernet(fernet_key)
    
    def get_current_key(self) -> Fernet:
        """获取当前版本的密钥"""
        if self._current_version not in self._keys:
            # 回退到使用settings.secret_key
            secret = str(get_settings().secret_key or "")
            digest = hashlib.sha256(secret.encode("utf-8")).digest()
            key = base64.urlsafe_b64encode(digest)
            return Fernet(key)
        return self._keys[self._current_version]
    
    def get_key(self, version: int) -> Optional[Fernet]:
        """获取指定版本的密钥"""
        return self._keys.get(version)
    
    def set_current_version(self, version: int) -> None:
        """设置当前密钥版本"""
        self._current_version = version
    
    def get_all_versions(self) -> list[int]:
        """获取所有密钥版本"""
        return sorted(self._keys.keys())
    
    def get_current_version(self) -> int:
        """获取当前密钥版本"""
        return self._current_version


# 全局密钥管理器实例
_key_manager = KeyManager()


def initialize_keys(secret_key: Optional[str] = None) -> None:
    """初始化密钥管理器
    
    Args:
        secret_key: 主密钥，如果为None则使用settings.secret_key
    """
    if secret_key is None:
        secret_key = str(get_settings().secret_key or "")
    
    # 添加版本1密钥（默认密钥）
    _key_manager.add_key(1, secret_key)
    _key_manager.set_current_version(1)


def rotate_key(new_key: str) -> int:
    """轮换密钥
    
    Args:
        new_key: 新密钥
    
    Returns:
        新密钥的版本号
    """
    current_version = _key_manager.get_current_version()
    new_version = current_version + 1
    
    _key_manager.add_key(new_version, new_key)
    _key_manager.set_current_version(new_version)
    
    return new_version


def _get_fernet(version: int | None = None) -> Fernet:
    """获取指定版本的Fernet实例"""
    key_version = version or _key_manager.get_current_version()
    fernet = _key_manager.get_key(key_version)
    if fernet is None:
        # 回退到当前版本
        fernet = _key_manager.get_current_key()
    return fernet


def encrypt_secret(raw: str, version: int | None = None) -> str:
    """加密密钥（支持指定版本密钥）
    
    Args:
        raw: 原始密钥
        version: 密钥版本，如果为None则使用当前版本
    
    Returns:
        加密后的密钥，格式: enc:v{version}:{token}
    """
    s = str(raw or "").strip()
    if not s:
        return ""
    if s.startswith(_ENC_PREFIX):
        return s
    
    key_version = version or _key_manager.get_current_version()
    fernet = _get_fernet(key_version)
    token = fernet.encrypt(s.encode("utf-8")).decode("utf-8")
    
    # 新格式: enc:v{version}:{token}
    return f"{_ENC_PREFIX}v{key_version}:{token}"


def decrypt_secret(value: str) -> str:
    """解密密钥（支持所有版本的密钥）
    
    Args:
        value: 加密的密钥
    
    Returns:
        解密后的密钥
    """
    s = str(value or "").strip()
    if not s:
        return ""
    if not s.startswith(_ENC_PREFIX):
        return s
    
    # 检查是否是旧格式（无版本号）
    if ":" not in s[len(_ENC_PREFIX):]:
        token = s[len(_ENC_PREFIX):]
        try:
            return _key_manager.get_current_key().decrypt(token.encode("utf-8")).decode("utf-8")
        except (InvalidToken, Exception):
            return ""
    
    # 新格式: enc:v{version}:{token}
    try:
        parts = s[len(_ENC_PREFIX):].split(":", 1)
        if len(parts) != 2:
            return ""
        
        version_part, token = parts
        if not version_part.startswith("v"):
            return ""
        
        version = int(version_part[1:])
        
        # 尝试使用指定版本解密
        fernet = _key_manager.get_key(version)
        if fernet is None:
            # 如果指定版本不存在，尝试使用当前版本
            fernet = _key_manager.get_current_key()
        
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError, Exception):
        return ""


def get_key_versions() -> list[int]:
    """获取所有密钥版本
    
    Returns:
        密钥版本列表
    """
    return _key_manager.get_all_versions()


def get_current_key_version() -> int:
    """获取当前密钥版本
    
    Returns:
        当前密钥版本号
    """
    return _key_manager.get_current_version()


# 初始化密钥管理器
initialize_keys()
