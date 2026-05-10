"""安全工具：密码加密和JWT
支持RS256（推荐）和HS256（仅开发环境）算法
"""
import logging
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Response
from typing import Literal

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# 确保算法只能是有效的值
Algorithm = Literal["RS256", "HS256"]

# 验证算法配置
if settings.algorithm not in ["RS256", "HS256"]:
    raise ValueError(
        f"Invalid JWT algorithm: {settings.algorithm}. "
        "Must be either 'RS256' (recommended for production) or 'HS256' (development only)."
    )


def hash_password(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def _get_jwt_key_and_algorithm() -> tuple[str, str]:
    """获取JWT密钥和算法
    
    Returns:
        (key, algorithm): 根据配置返回相应的密钥和算法
    """
    algorithm = settings.algorithm
    
    if algorithm == "RS256":
        # RS256使用非对称加密：签名用私钥，验证用公钥
        if not settings.jwt_rsa_private_key:
            raise ValueError(
                "JWT_RSA_PRIVATE_KEY must be set for RS256 algorithm. "
                "See configuration error messages for key generation instructions."
            )
        return settings.jwt_rsa_private_key, algorithm
    else:
        # HS256使用对称加密
        if not settings.secret_key:
            raise ValueError(
                "SECRET_KEY must be set for HS256 algorithm. "
                "HS256 is not recommended for production - consider upgrading to RS256."
            )
        return settings.secret_key, algorithm


def create_access_token(
        data: dict[str, object],
        expires_delta: timedelta | None = None,
        audience: str | None = None) -> str:
    """创建JWT访问令牌

    Args:
        data: 要编码的数据
        expires_delta: 自定义过期时间
        audience: 令牌受众（用于区分不同用途的token）
    
    Returns:
        编码后的JWT令牌字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(
            timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    if "type" not in to_encode:
        to_encode["type"] = "access"
    if audience:
        to_encode.update({"aud": audience})

    # 根据配置获取相应的密钥和算法
    key, algorithm = _get_jwt_key_and_algorithm()
    
    encoded_jwt = jwt.encode(to_encode, key, algorithm=algorithm)

    return encoded_jwt


def decode_token(token: str, audience: str | None = None) -> dict[str, object] | None:
    """解码JWT令牌
    
    Args:
        token: JWT令牌字符串
    
    Returns:
        解码后的payload，如果无效返回None
    """
    try:
        algorithm = settings.algorithm
        
        if algorithm == "RS256":
            # RS256使用公钥验证
            if not settings.jwt_rsa_public_key:
                raise ValueError(
                    "JWT_RSA_PUBLIC_KEY must be set for RS256 algorithm."
                )
            payload = jwt.decode(
                token,
                settings.jwt_rsa_public_key,
                algorithms=[algorithm],
                options={"verify_aud": False}  # 允许缺少aud的旧token
            )
        else:
            # HS256使用对称密钥
            if not settings.secret_key:
                raise ValueError(
                    "SECRET_KEY must be set for HS256 algorithm."
                )
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[algorithm],
                options={"verify_aud": False}
            )
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> dict[str, object] | None:
    """解码并验证访问令牌

    - 兼容历史访问令牌（缺少 type 时允许）
    - 明确拒绝 refresh/share 等非访问令牌
    """
    payload = decode_token(token)
    if payload is None:
        return None

    token_type = str(payload.get("type") or "").strip()
    if token_type and token_type != "access":
        return None

    return payload


def create_refresh_token(
        data: dict[str, object], expires_delta: timedelta | None = None) -> str:
    """创建JWT刷新令牌

    Args:
        data: 要编码的数据（包含用户标识）
        expires_delta: 自定义过期时间（默认7天）

    Returns:
        编码后的刷新令牌字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)

    to_encode.update({"exp": expire, "type": "refresh"})
    
    # 根据配置获取相应的密钥和算法
    key, algorithm = _get_jwt_key_and_algorithm()
    
    encoded_jwt = jwt.encode(to_encode, key, algorithm=algorithm)

    return encoded_jwt


def decode_refresh_token(token: str) -> dict[str, object] | None:
    """解码并验证刷新令牌

    Args:
        token: 刷新令牌字符串

    Returns:
        解码后的payload，如果无效返回None
    """
    try:
        algorithm = settings.algorithm
        
        if algorithm == "RS256":
            if not settings.jwt_rsa_public_key:
                raise ValueError("JWT_RSA_PUBLIC_KEY must be set for RS256 algorithm.")
            payload = jwt.decode(
                token,
                settings.jwt_rsa_public_key,
                algorithms=[algorithm],
                options={"verify_aud": False}
            )
        else:
            if not settings.secret_key:
                raise ValueError("SECRET_KEY must be set for HS256 algorithm.")
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[algorithm],
                options={"verify_aud": False}
            )

        # 验证是否为刷新令牌类型
        if payload.get("type") != "refresh":
            return None

        return payload
    except JWTError:
        return None


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """设置httpOnly Cookie用于认证

    Args:
        response: FastAPI响应对象
        access_token: JWT访问令牌
        refresh_token: JWT刷新令牌
    """
    # 设置access_token Cookie（1小时）
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # 防止JavaScript访问，避免XSS攻击
        secure=not settings.debug,  # 生产环境仅HTTPS
        samesite="strict",  # 严格的同站策略
        max_age=60 * 60,  # 1小时
        path="/"
    )

    # 设置refresh_token Cookie（7天）
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,  # 防止JavaScript访问
        secure=not settings.debug,  # 生产环境仅HTTPS
        samesite="strict",  # 严格的同站策略
        max_age=7 * 24 * 60 * 60,  # 7天
        path="/"
    )


# ==================== Token Rotation (Token轮换机制) ====================

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.cache_service import CacheService


def _get_cache_service() -> "CacheService | None":
    """获取缓存服务实例"""
    try:
        from app.services.cache_service import cache_service
        return cache_service
    except Exception:
        return None


def _get_token_jti(payload: dict[str, object]) -> str | None:
    """获取Token的唯一标识符 (JWT ID)
    
    Args:
        payload: JWT payload
        
    Returns:
        jti (JWT ID) 或 None
    """
    jti = payload.get("jti")
    if jti:
        return str(jti)
    # 如果没有jti，使用sub和exp的组合作为唯一标识
    sub = payload.get("sub")
    exp = payload.get("exp")
    if sub and exp:
        return f"{sub}:{exp}"
    return None


async def is_token_revoked(token: str) -> bool:
    """检查token是否已被撤销
    
    Args:
        token: JWT令牌
        
    Returns:
        True if token is revoked
    """
    cache = _get_cache_service()
    if not cache or not cache.is_connected:
        # 如果没有缓存服务，默认不撤销（降级处理）
        return False
    
    try:
        payload = decode_token(token)
        if not payload:
            return True  # 无效token视为已撤销
        
        jti = _get_token_jti(payload)
        if not jti:
            return False
        
        revoked = await cache.get(f"token:revoked:{jti}")
        return revoked is not None
    except (ConnectionError, TimeoutError) as e:
        # 缓存连接错误，降级处理
        logger.warning(f"Cache connection error while checking token revocation: {e}")
        return False
    except Exception as e:
        logger.warning(f"Failed to check token revocation status: {e}")
        return False


async def revoke_token(token: str, expire_seconds: int = 7 * 24 * 60 * 60) -> None:
    """撤销token（加入黑名单）
    
    Args:
        token: 要撤销的JWT令牌
        expire_seconds: 黑名单过期时间（默认7天）
    """
    cache = _get_cache_service()
    if not cache or not cache.is_connected:
        logger.debug("Cache not available, skipping token revocation")
        return
    
    try:
        payload = decode_token(token)
        if not payload:
            logger.debug("Cannot revoke invalid token")
            return
        
        jti = _get_token_jti(payload)
        if not jti:
            logger.debug("Token has no JTI, cannot revoke")
            return
        
        await cache.set(f"token:revoked:{jti}", "1", expire=expire_seconds)
        logger.info(f"Token revoked: {jti}")
    except (ConnectionError, TimeoutError) as e:
        # 缓存连接错误
        logger.warning(f"Cache connection error while revoking token: {e}")
    except Exception as e:
        logger.warning(f"Failed to revoke token: {e}")


async def rotate_tokens(
    refresh_token: str,
    user_id: int,
    user_email: str,
    user_role: str = "user"
) -> dict[str, str] | None:
    """Token轮换 - 使用refresh token换取新的token对
    
    实现机制：
    1. 验证refresh token的有效性
    2. 检查token是否已被撤销（防止重放攻击）
    3. 撤销旧的refresh token
    4. 生成新的access_token和refresh_token
    
    Args:
        refresh_token: 当前的刷新令牌
        user_id: 用户ID
        user_email: 用户邮箱
        user_role: 用户角色
        
    Returns:
        包含新token的字典，如果失败返回None
    """
    # 1. 验证refresh token
    payload = decode_refresh_token(refresh_token)
    if not payload:
        logger.warning("Token rotation failed: invalid refresh token")
        return None
    
    # 2. 检查token是否已被撤销
    if await is_token_revoked(refresh_token):
        logger.warning("Token rotation failed: token already revoked (possible replay attack)")
        return None
    
    # 3. 验证payload中的用户ID是否匹配
    token_user_id = payload.get("sub")
    if not token_user_id or int(str(token_user_id)) != user_id:
        logger.warning("Token rotation failed: user ID mismatch")
        return None
    
    # 4. 撤销旧的refresh token
    await revoke_token(refresh_token)
    
    # 5. 生成新的token对
    token_data = {
        "sub": user_id,
        "email": user_email,
        "role": user_role,
    }
    
    # 添加jti用于唯一标识token
    import uuid
    new_access_token = create_access_token(
        {**token_data, "jti": str(uuid.uuid4())}
    )
    new_refresh_token = create_refresh_token(
        {**token_data, "jti": str(uuid.uuid4())}
    )
    
    logger.info(f"Token rotated for user {user_id}")
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
    }


def create_token_pair(
    user_id: int,
    user_email: str,
    user_role: str = "user"
) -> dict[str, str]:
    """创建新的token对（登录时使用）
    
    Args:
        user_id: 用户ID
        user_email: 用户邮箱
        user_role: 用户角色
        
    Returns:
        包含access_token和refresh_token的字典
    """
    import uuid
    
    token_data = {
        "sub": user_id,
        "email": user_email,
        "role": user_role,
    }
    
    access_token = create_access_token(
        {**token_data, "jti": str(uuid.uuid4())}
    )
    refresh_token = create_refresh_token(
        {**token_data, "jti": str(uuid.uuid4())}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def clear_auth_cookies(response: Response) -> None:
    """清除认证Cookie

    Args:
        response: FastAPI响应对象
    """
    response.delete_cookie(
        key="access_token",
        path="/"
    )
    response.delete_cookie(
        key="refresh_token",
        path="/"
    )


# ==================== URL 安全验证 (SSRF 防护) ====================

def validate_external_url(url: str, allowed_schemes: set[str] | None = None) -> bool:
    """
    验证外部URL是否合法，防止 SSRF 攻击
    
    Args:
        url: 要验证的 URL
        allowed_schemes: 允许的协议集合，默认只允许 http/https
        
    Returns:
        bool: URL 是否合法
    """
    from urllib.parse import urlparse
    import ipaddress
    
    if not url:
        return False
    
    if allowed_schemes is None:
        allowed_schemes = {"http", "https"}
    
    try:
        parsed = urlparse(url)
        
        # 检查协议
        if parsed.scheme not in allowed_schemes:
            logger.warning(f"URL rejected: invalid scheme {parsed.scheme}")
            return False
        
        # 检查是否为空主机
        if not parsed.hostname:
            logger.warning("URL rejected: empty hostname")
            return False
        
        hostname = parsed.hostname.lower()
        
        # 禁止 localhost
        if hostname in {"localhost", "127.0.0.1", "::1", "0:0:0:0:0:0:0:1"}:
            logger.warning("URL rejected: localhost not allowed")
            return False
        
        # 检查端口（禁止访问敏感端口）
        port = parsed.port
        if port is not None:
            blocked_ports = {
                22,    # SSH
                23,    # Telnet
                25,    # SMTP
                53,    # DNS
                110,   # POP3
                143,   # IMAP
                3306,  # MySQL
                3389,  # RDP
                5432,  # PostgreSQL
                6379,  # Redis
                9200,  # Elasticsearch
                27017, # MongoDB
            }
            if port in blocked_ports:
                logger.warning(f"URL rejected: blocked port {port}")
                return False
        
        # 检查是否为内网 IP
        try:
            ip = ipaddress.ip_address(hostname)
            # 检查是否为私有地址
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_multicast:
                logger.warning(f"URL rejected: internal IP {hostname}")
                return False
        except ValueError:
            # 不是 IP 地址，是域名，继续检查
            pass
        
        return True
        
    except Exception as e:
        logger.warning(f"URL validation failed: {e}")
        return False


def validate_rss_url(url: str) -> bool:
    """
    验证 RSS 订阅 URL 是否合法
    
    Args:
        url: RSS URL
        
    Returns:
        bool: URL 是否合法
    """
    return validate_external_url(url)


def validate_sherpa_remote_url(url: str) -> bool:
    """
    验证 Sherpa ASR 远程服务 URL 是否合法
    
    Args:
        url: Sherpa 远程服务 URL
        
    Returns:
        bool: URL 是否合法
    """
    # Sherpa 服务通常只允许 http/https，且需要更严格的验证
    if not validate_external_url(url):
        return False
    
    # 可以添加额外的白名单检查
    # 例如只允许特定的域名后缀
    from urllib.parse import urlparse
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    
    # 禁止直接访问 IP 地址（可选，根据实际需求调整）
    import ipaddress
    try:
        ipaddress.ip_address(hostname)
        logger.warning("Sherpa URL rejected: direct IP not allowed")
        return False
    except ValueError:
        pass
    
    return True
