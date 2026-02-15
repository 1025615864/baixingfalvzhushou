"""
日志脱敏处理模块

提供敏感信息过滤功能，防止日志泄露敏感数据
"""
import hashlib
import re
from urllib.parse import urlparse, parse_qs, urlencode


# 需要过滤的敏感参数（URL query和headers）
SENSITIVE_PARAMS = {
    'token', 'password', 'api_key', 'secret', 'access_token', 'refresh_token',
    'authorization', 'card_number', 'cvv', 'expiry_date', 'phone', 'email',
    'id_card', 'social_security', 'ssn', 'credit_card', 'bank_account',
    'private_key', 'certificate', 'cookie', 'session', 'csrf_token'
}

# 需要过滤的敏感headers
SENSITIVE_HEADERS = {
    'authorization', 'cookie', 'x-api-key', 'x-auth-token', 'x-csrf-token',
    'x-request-token', 'api-key', 'apikey', 'secret-key', 'session-id'
}

# 脱敏占位符
MASK_PLACEHOLDER = "***FILTERED***"


def sanitize_url(url: str) -> str:
    """
    过滤URL中的敏感参数
    
    Args:
        url: 原始URL
        
    Returns:
        脱敏后的URL
        
    Example:
        >>> sanitize_url("https://api.example.com/users?token=abc123&page=1")
        'https://api.example.com/users?token=***FILTERED***&page=1'
    """
    if not url:
        return url
    
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return url
        
        params = parse_qs(parsed.query)
        sanitized = {}
        
        for key, values in params.items():
            key_lower = key.lower()
            # 检查是否是敏感参数
            if any(sensitive in key_lower for sensitive in SENSITIVE_PARAMS):
                sanitized[key] = [MASK_PLACEHOLDER]
            else:
                sanitized[key] = values
        
        # 重建query字符串
        new_query = urlencode(sanitized, doseq=True)
        
        # 重建URL
        return parsed._replace(query=new_query).geturl()
    except Exception:
        # 解析失败时返回原始URL
        return url


def sanitize_headers(headers: dict) -> dict:
    """
    过滤HTTP头中的敏感信息
    
    Args:
        headers: HTTP头字典
        
    Returns:
        脱敏后的HTTP头字典
    """
    if not headers:
        return headers
    
    sanitized = {}
    for key, value in headers.items():
        key_lower = key.lower()
        if key_lower in SENSITIVE_HEADERS:
            sanitized[key] = MASK_PLACEHOLDER
        else:
            # 检查header值是否包含敏感信息
            sanitized[key] = _mask_sensitive_in_string(str(value))
    
    return sanitized


def sanitize_ip(ip: str) -> str:
    """
    IP地址脱敏
    
    保留前两段，后两段用*替换
    
    Args:
        ip: IP地址
        
    Returns:
        脱敏后的IP地址
        
    Example:
        >>> sanitize_ip("192.168.1.100")
        '192.168.*.*'
    """
    if not ip:
        return "unknown"
    
    # IPv4处理
    if '.' in ip and ':' not in ip:
        parts = ip.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.*.*"
    
    # IPv6完全过滤
    if ':' in ip:
        return MASK_PLACEHOLDER
    
    return "unknown"


def hash_user_id(user_id: int | str | None) -> str:
    """
    对用户ID进行哈希处理
    
    Args:
        user_id: 用户ID
        
    Returns:
        哈希后的用户ID字符串
    """
    if user_id is None:
        return "anonymous"
    
    # 使用SHA256哈希，取前16位
    hash_str = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]
    return hash_str


def _mask_sensitive_in_string(value: str) -> str:
    """
    在字符串中检测并脱敏敏感信息
    
    Args:
        value: 原始字符串
        
    Returns:
        脱敏后的字符串
    """
    if not value:
        return value
    
    # 检测并脱敏可能的token
    # Bearer token
    if re.match(r'^[Bb]earer\s+', value):
        return f"Bearer {MASK_PLACEHOLDER}"
    
    # Basic auth
    if re.match(r'^[Bb]asic\s+', value):
        return f"Basic {MASK_PLACEHOLDER}"
    
    # JWT token (三段式，以eyJ开头)
    if re.match(r'^eyJ[\w-]*\.[\w-]*\.[\w-]*$', value):
        return MASK_PLACEHOLDER
    
    # API Key格式
    if re.match(r'^(sk-|pk-|ak-)[\w-]+$', value):
        return MASK_PLACEHOLDER
    
    return value


def sanitize_body(body: dict | str | None) -> dict | str | None:
    """
    脱敏请求/响应体中的敏感信息
    
    Args:
        body: 请求或响应体
        
    Returns:
        脱敏后的body
    """
    if body is None:
        return None
    
    if isinstance(body, str):
        # 尝试解析JSON
        try:
            import json
            body_dict = json.loads(body)
            return json.dumps(_sanitize_dict(body_dict))
        except (json.JSONDecodeError, ValueError):
            # 不是JSON，直接返回
            return body
    
    if isinstance(body, dict):
        return _sanitize_dict(body)
    
    return body


def _sanitize_dict(data: dict) -> dict:
    """
    递归脱敏字典中的敏感信息
    
    Args:
        data: 字典数据
        
    Returns:
        脱敏后的字典
    """
    if not isinstance(data, dict):
        return data
    
    result = {}
    for key, value in data.items():
        key_lower = str(key).lower()
        
        # 检查key是否敏感
        if any(sensitive in key_lower for sensitive in SENSITIVE_PARAMS):
            result[key] = MASK_PLACEHOLDER
        elif isinstance(value, dict):
            result[key] = _sanitize_dict(value)
        elif isinstance(value, list):
            result[key] = [_sanitize_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    
    return result
