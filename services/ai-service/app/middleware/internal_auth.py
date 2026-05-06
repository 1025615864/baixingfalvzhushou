"""AI服务内部API Key认证 - 用于服务间调用"""
import os
import logging
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "internal-api-key-change-in-production")
API_KEY_HEADER = APIKeyHeader(name="X-Internal-API-Key", auto_error=False)


async def verify_internal_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """验证内部API Key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少内部API Key"
        )

    if api_key != INTERNAL_API_KEY:
        logger.warning(f"Invalid internal API key attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无效的内部API Key"
        )

    return api_key


def check_internal_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> bool:
    """检查API Key是否有效（不抛出异常）"""
    if not api_key:
        return False
    return api_key == INTERNAL_API_KEY
