"""敏感操作二次验证工具

提供敏感操作二次验证功能。
"""
from __future__ import annotations

import time
from typing import Optional

from fastapi import HTTPException, Request, status


class VerificationRequiredError(Exception):
    """需要二次验证"""
    pass


class VerificationToken:
    """验证令牌"""

    def __init__(
        self,
        user_id: int,
        operation: str,
        expires_in: int = 300  # 5分钟过期
    ) -> None:
        self.user_id = user_id
        self.operation = operation
        self.created_at = time.time()
        self.expires_at = self.created_at + expires_in
        self.verified = False

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > self.expires_at

    def verify(self) -> None:
        """验证操作"""
        if self.is_expired():
            raise VerificationRequiredError("验证令牌已过期")
        self.verified = True


class VerificationManager:
    """验证管理器"""

    def __init__(self) -> None:
        self._tokens: dict[str, VerificationToken] = {}
        self._last_cleanup: float = time.time()

    def _cleanup_expired_tokens(self) -> None:
        """清理过期令牌"""
        current_time = time.time()
        if current_time - self._last_cleanup < 60:  # 每分钟清理一次
            return

        expired_tokens = [
            key for key, token in self._tokens.items()
            if token.is_expired()
        ]
        for key in expired_tokens:
            del self._tokens[key]

        self._last_cleanup = current_time

    def create_token(
        self,
        user_id: int,
        operation: str
    ) -> str:
        """创建验证令牌"""
        self._cleanup_expired_tokens()

        token = VerificationToken(user_id=user_id, operation=operation)
        token_key = f"{user_id}:{operation}:{int(time.time())}"
        self._tokens[token_key] = token

        return token_key

    def verify_token(
        self,
        token_key: str,
        user_id: int
    ) -> None:
        """验证令牌"""
        self._cleanup_expired_tokens()

        token = self._tokens.get(token_key)
        if token is None:
            raise VerificationRequiredError("验证令牌不存在")

        if token.user_id != user_id:
            raise VerificationRequiredError("验证令牌无效")

        token.verify()

    def is_verified(
        self,
        token_key: str,
        user_id: int
    ) -> bool:
        """检查是否已验证"""
        self._cleanup_expired_tokens()

        token = self._tokens.get(token_key)
        if token is None:
            return False

        if token.user_id != user_id:
            return False

        return token.verified


# 全局验证管理器
verification_manager = VerificationManager()


def require_verification(
    operation: str,
    request: Request
) -> Optional[str]:
    """要求二次验证

    Args:
        operation: 操作名称
        request: 请求对象

    Returns:
        验证令牌，如果需要验证
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录"
        )

    # 检查是否已有验证令牌
    verification_token = request.headers.get("X-Verification-Token")
    if verification_token:
        try:
            verification_manager.verify_token(verification_token, user_id)
            return None
        except VerificationRequiredError:
            pass

    # 创建新的验证令牌
    token_key = verification_manager.create_token(user_id, operation)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "message": "需要二次验证",
            "verification_token": token_key,
            "operation": operation,
        }
    )


def check_verification(
    operation: str,
    request: Request
) -> bool:
    """检查是否已验证

    Args:
        operation: 操作名称
        request: 请求对象

    Returns:
        是否已验证
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        return False

    verification_token = request.headers.get("X-Verification-Token")
    if not verification_token:
        return False

    return verification_manager.is_verified(verification_token, user_id)
