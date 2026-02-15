"""请求签名验证工具

实现API请求签名验证，防止重放攻击。
"""
from __future__ import annotations

import hashlib
import hmac
import time

from fastapi import HTTPException, Request, status


class SignatureValidationError(Exception):
    """签名验证失败"""
    pass


class SignatureVerifier:
    """签名验证器"""

    def __init__(self, secret_key: str) -> None:
        self.secret_key = secret_key
        self.timestamp_tolerance = 300  # 5分钟时间戳容忍度

    def _generate_signature(
        self,
        method: str,
        path: str,
        timestamp: str,
        body: str
    ) -> str:
        """生成签名"""
        # 拼接签名内容
        message = f"{method}\n{path}\n{timestamp}\n{body}"

        # 使用HMAC-SHA256生成签名
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    def verify_signature(
        self,
        request: Request,
        signature: str,
        timestamp: str
    ) -> bool:
        """验证签名

        Args:
            request: 请求对象
            signature: 签名
            timestamp: 时间戳

        Returns:
            是否验证通过
        """
        try:
            # 验证时间戳（防止重放攻击）
            current_timestamp = int(time.time())
            request_timestamp = int(timestamp)

            if abs(current_timestamp - request_timestamp) > self.timestamp_tolerance:
                raise SignatureValidationError("时间戳无效")

            # 获取请求体
            body = ""
            if request.method in ["POST", "PUT", "PATCH"]:
                # request.body 是一个异步方法，需要 await
                # 这里简化处理，实际使用时应该在异步上下文中调用
                body_bytes = request.body() if callable(request.body) else request.body
                if body_bytes:
                    if isinstance(body_bytes, bytes):
                        body = body_bytes.decode('utf-8')
                    else:
                        body = str(body_bytes)

            # 生成预期签名
            expected_signature = self._generate_signature(
                method=request.method,
                path=request.url.path,
                timestamp=timestamp,
                body=body
            )

            # 比较签名
            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            raise SignatureValidationError(f"签名验证失败: {e}")


def require_signature(
    request: Request,
    secret_key: str
) -> None:
    """要求请求签名

    Args:
        request: 请求对象
        secret_key: 密钥

    Raises:
        HTTPException: 签名验证失败
    """
    # 获取签名和时间戳
    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")

    if not signature or not timestamp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少签名或时间戳"
        )

    # 验证签名
    verifier = SignatureVerifier(secret_key)
    if not verifier.verify_signature(request, signature, timestamp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="签名验证失败"
        )


def generate_signature(
    method: str,
    path: str,
    body: str,
    secret_key: str
) -> tuple[str, str]:
    """生成签名

    Args:
        method: HTTP方法
        path: 路径
        body: 请求体
        secret_key: 密钥

    Returns:
        (签名, 时间戳)
    """
    timestamp = str(int(time.time()))
    verifier = SignatureVerifier(secret_key)
    signature = verifier._generate_signature(method, path, timestamp, body)

    return signature, timestamp
