"""CSRF防护工具"""
import secrets
import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Optional

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def generate_csrf_token(session_id: str) -> str:
    """
    生成CSRF token
    
    Args:
        session_id: 会话ID或用户ID
    
    Returns:
        CSRF token字符串
    """
    # 生成随机salt
    salt = secrets.token_hex(16)
    timestamp = int(datetime.now().timestamp())
    
    # 组合: timestamp:salt:session_id
    raw = f"{timestamp}:{salt}:{session_id}"
    
    # 使用专用CSRF密钥签名（与JWT密钥分离）
    key = settings.csrf_secret_key.encode('utf-8')
    signature = hmac.new(key, raw.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # 最终token: timestamp:salt:signature
    return f"{raw}:{signature}"


def validate_csrf_token(token: str, session_id: str) -> bool:
    """
    验证CSRF token
    
    Args:
        token: 要验证的token
        session_id: 会话ID或用户ID
    
    Returns:
        是否有效
    """
    if not token or not session_id:
        return False
    
    try:
        parts = token.split(':')
        if len(parts) != 4:
            logger.warning(f"Invalid CSRF token format: {len(parts)} parts")
            return False
        
        timestamp_str, salt, stored_session_id, signature = parts
        
        # 验证session_id匹配
        if stored_session_id != session_id:
            logger.warning("CSRF token session_id mismatch")
            return False
        
        # 验证token时效性
        try:
            timestamp = int(timestamp_str)
            token_age = datetime.now().timestamp() - timestamp
            max_age = settings.csrf_token_expire_hours * 3600
            
            if token_age > max_age:
                logger.warning(f"CSRF token expired: age={token_age}s, max={max_age}s")
                return False
                
            if token_age < 0:
                logger.warning("CSRF token expiration time in the future")
                return False
                
        except ValueError:
            logger.warning("Invalid CSRF token timestamp")
            return False
        
        # 验证签名（使用专用CSRF密钥）
        key = settings.csrf_secret_key.encode('utf-8')
        raw = f"{timestamp_str}:{salt}:{session_id}"
        expected_signature = hmac.new(key, raw.encode('utf-8'), hashlib.sha256).hexdigest()
        
        # 使用恒定时间比较防止时序攻击
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("CSRF token signature verification failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"CSRF token validation error: {e}")
        return False


def get_csrf_token_error_message() -> str:
    """获取CSRF token验证失败的标准错误消息"""
    return "CSRF token验证失败。请刷新页面后重试。"


def should_validate_csrf(method: str, path: str) -> bool:
    """
    判断是否需要验证CSRF
    
    Args:
        method: HTTP方法
        path: 请求路径
    
    Returns:
        是否需要验证
    """
    if not settings.csrf_enabled:
        return False
    
    # 检查方法是否需要保护
    if method not in settings.csrf_protected_methods:
        return False
    
    # 检查路径是否在豁免列表中
    for exempt_path in settings.csrf_exempt_paths:
        if path.startswith(exempt_path):
            return False
    
    return True


CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"