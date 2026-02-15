"""CSRF防护中间件"""
import logging
from collections.abc import Awaitable, Callable
from fastapi import Request, HTTPException, Response, status

from ..utils.csrf import (
    validate_csrf_token,
    should_validate_csrf,
    get_csrf_token_error_message,
    CSRF_HEADER_NAME,
)
from ..utils.security import decode_access_token

logger = logging.getLogger(__name__)


async def csrf_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    CSRF防护中间件
    
    验证所有状态改变的请求（POST, PUT, PATCH, DELETE）包含有效的CSRF token
    """
    # 获取请求信息
    method = request.method.upper()
    path = request.url.path
    
    # 判断是否需要验证CSRF
    if not should_validate_csrf(method, path):
        return await call_next(request)

    if not request.cookies.get("access_token"):
        return await call_next(request)
    
    # 尝试从多个来源获取token
    # 1. 从header获取
    csrf_token = request.headers.get(CSRF_HEADER_NAME)
    
    # 2. 如果header中没有，尝试从form data获取
    if not csrf_token and request.headers.get("content-type", "").startswith("multipart/form-data"):
        try:
            form_data = await request.form()
            token_value = form_data.get("csrf_token")
            # 确保是字符串类型，而不是UploadFile
            if token_value and hasattr(token_value, "read"):
                # 这是UploadFile，跳过
                pass
            elif token_value:
                csrf_token = str(token_value)
        except Exception:
            logger.exception("Failed to extract CSRF token from cookie")
    
    # 注意：不再支持从query参数获取CSRF token
    # 原因：query参数会被记录在浏览器历史、服务器日志、Referer中，导致token泄露
    # 只应从header或form data获取CSRF token
    
    # 获取用户ID作为session_id
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        try:
            auth = str(request.headers.get("authorization") or "").strip()
            token = None
            if auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1].strip()
            if not token:
                token = request.cookies.get("access_token")
            if token:
                payload = decode_access_token(token)
                sub = payload.get("sub") if payload else None
                if sub is not None:
                    user_id = int(str(sub))
        except Exception:
            logger.exception("Failed to extract user_id from token")
    session_id = str(user_id) if user_id else request.client.host if request.client else "unknown"
    
    # 验证token
    if not csrf_token:
        logger.warning(f"CSRF token missing: {method} {path} from {session_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "CSRF token missing", "message": get_csrf_token_error_message()},
        )
    
    if not validate_csrf_token(csrf_token, session_id):
        logger.warning(f"CSRF token invalid: {method} {path} from {session_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "CSRF token invalid", "message": get_csrf_token_error_message()},
        )
    
    # CSRF验证通过，继续处理请求
    return await call_next(request)


def get_csrf_exclude_paths() -> list[str]:
    """获取CSRF豁免路径列表（用于文档）"""
    from ..config import get_settings
    settings = get_settings()
    return settings.csrf_exempt_paths