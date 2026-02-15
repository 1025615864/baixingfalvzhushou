"""TOTP 双因素认证服务"""
from __future__ import annotations

import base64
import hashlib
import secrets
import uuid
from typing import NamedTuple

import pyotp
from cryptography.fernet import Fernet

from ..config import settings


class TOTPSetupResult(NamedTuple):
    """TOTP 设置结果"""
    secret: str
    uri: str
    backup_codes: list[str]


class TOTPService:
    """TOTP 双因素认证服务"""

    def __init__(self) -> None:
        """初始化 TOTP 服务"""
        self._init_encryption()

    def _init_encryption(self) -> None:
        """初始化加密密钥"""
        # 从环境变量获取加密密钥，如果没有则生成一个（仅用于开发）
        encryption_key = getattr(settings, 'SECURITY_ENCRYPTION_KEY', None)
        if encryption_key:
            # 确保密钥是 32 字节长度（Fernet 要求）
            key_bytes = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
            if len(key_bytes) < 32:
                # 使用 SHA-256 哈希来确保 32 字节
                key_bytes = hashlib.sha256(key_bytes).digest()
            # 转换为 Base64 格式（Fernet 要求）
            key_b64 = base64.urlsafe_b64encode(key_bytes[:32])
            self._cipher = Fernet(key_b64)
        else:
            # 开发环境：生成临时密钥
            # 注意：生产环境必须设置 SECURITY_ENCRYPTION_KEY
            self._cipher = Fernet(Fernet.generate_key())

    def generate_secret(self) -> str:
        """生成 TOTP 密钥（32位 base32）
        
        Returns:
            str: 生成的 base32 编码密钥
        """
        # pyotp 生成 32 字符的 base32 密钥
        return pyotp.random_base32()

    def generate_provisioning_uri(
        self,
        secret: str,
        username: str,
        issuer: str = "百姓法律助手"
    ) -> str:
        """生成二维码 URI（符合 Google Authenticator 标准）
        
        Args:
            secret: TOTP 密钥
            username: 用户名
            issuer: 应用名称
            
        Returns:
            str: provisioning URI
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=username,
            issuer_name=issuer
        )

    def verify_code(self, secret: str, code: str, window: int = 1) -> bool:
        """验证 TOTP 码
        
        Args:
            secret: TOTP 密钥
            code: 用户输入的验证码
            window: 时间窗口容忍度（默认前后1个时间窗口）
            
        Returns:
            bool: 验证是否成功
        """
        if not code or not secret:
            return False
        
        # 清理输入（移除空格）
        code = code.strip().replace(" ", "")
        
        # 必须是 6 位数字
        if not code.isdigit() or len(code) != 6:
            return False
        
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=window)
        except Exception:
            return False

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """生成备用验证码
        
        生成指定数量的随机备用码，每个备用码为 8 位数字，
        格式为 XXXX-XXXX 便于用户阅读。
        
        Args:
            count: 备用码数量（默认 10 个）
            
        Returns:
            list[str]: 备用码列表
        """
        codes: list[str] = []
        for _ in range(count):
            # 生成 8 位随机数字
            code = ''.join(secrets.choice('0123456789') for _ in range(8))
            # 格式化为 XXXX-XXXX
            formatted = f"{code[:4]}-{code[4:]}"
            codes.append(formatted)
        return codes

    def verify_backup_code(self, backup_codes: list[str], code: str) -> bool:
        """验证备用码
        
        Args:
            backup_codes: 存储的备用码列表
            code: 用户输入的备用码
            
        Returns:
            bool: 验证是否成功
        """
        if not code or not backup_codes:
            return False
        
        # 规范化输入（移除空格和连字符，转为大写）
        normalized_input = code.strip().replace("-", "").replace(" ", "").upper()
        
        for stored_code in backup_codes:
            normalized_stored = stored_code.replace("-", "").replace(" ", "").upper()
            if secrets.compare_digest(normalized_input, normalized_stored):
                return True
        
        return False

    def remove_used_backup_code(
        self,
        backup_codes: list[str],
        code: str
    ) -> list[str]:
        """移除已使用的备用码
        
        Args:
            backup_codes: 备用码列表
            code: 已使用的备用码
            
        Returns:
            list[str]: 更新后的备用码列表
        """
        normalized_input = code.strip().replace("-", "").replace(" ", "").upper()
        
        return [
            stored_code for stored_code in backup_codes
            if stored_code.replace("-", "").replace(" ", "").upper() != normalized_input
        ]

    def encrypt_secret(self, secret: str) -> str:
        """加密 TOTP 密钥
        
        Args:
            secret: 明文密钥
            
        Returns:
            str: 加密后的密钥
        """
        encrypted = self._cipher.encrypt(secret.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt_secret(self, encrypted_secret: str) -> str | None:
        """解密 TOTP 密钥
        
        Args:
            encrypted_secret: 加密后的密钥
            
        Returns:
            str | None: 解密后的密钥，失败返回 None
        """
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_secret.encode())
            decrypted = self._cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception:
            return None

    def generate_device_fingerprint(self, user_agent: str, ip: str) -> str:
        """生成设备指纹
        
        Args:
            user_agent: 用户代理字符串
            ip: IP 地址
            
        Returns:
            str: 设备指纹
        """
        # 组合用户代理和 IP，生成哈希
        data = f"{user_agent}:{ip}"
        fingerprint = hashlib.sha256(data.encode()).hexdigest()[:32]
        return fingerprint

    def setup_totp(self, username: str) -> TOTPSetupResult:
        """初始化 TOTP 设置
        
        生成密钥、URI 和备用码。
        
        Args:
            username: 用户名
            
        Returns:
            TOTPSetupResult: 设置结果
        """
        secret = self.generate_secret()
        uri = self.generate_provisioning_uri(secret, username)
        backup_codes = self.generate_backup_codes()
        
        return TOTPSetupResult(
            secret=secret,
            uri=uri,
            backup_codes=backup_codes
        )

    def get_current_code(self, secret: str) -> str:
        """获取当前时间窗口的 TOTP 码（用于测试）
        
        Args:
            secret: TOTP 密钥
            
        Returns:
            str: 当前验证码
        """
        totp = pyotp.TOTP(secret)
        return totp.now()


# 全局服务实例
totp_service = TOTPService()