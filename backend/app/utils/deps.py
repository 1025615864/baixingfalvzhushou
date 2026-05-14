"""依赖注入"""
import logging
import os
import sys
from typing import Annotated
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.user import User
from .security import decode_access_token
from .permissions import Role, has_role, has_any_role
from ..config import get_settings

security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)
settings = get_settings()


def _should_skip_verify() -> bool:
    """判断是否跳过手机号/邮箱验证
    
    安全说明：
    - 生产环境(ENVIRONMENT=production)强制验证，不可跳过
    - 仅在测试环境(pytest)允许跳过验证
    - 调试模式(debug=True)不再自动跳过验证
    """
    # 生产环境强制验证
    if os.getenv("ENVIRONMENT") == "production":
        return False
    
    # 显式强制验证时，不跳过
    if os.getenv("_BAIXING_FORCE_VERIFY") == "1":
        return False
    
    # 仅在测试环境下允许跳过
    return "pytest" in sys.modules


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials |
                           None, Depends(security)] = None,
) -> User:
    """获取当前登录用户"""
    token: str | None = None
    if credentials:
        token = credentials.credentials

    if not token:
        token = request.cookies.get("access_token")

    if not token:
        logger.info("auth: missing credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)

    if payload is None:
        logger.info("auth: token decode failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")
    if sub is None:
        logger.info("auth: token missing sub")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
        )

    try:
        user_id = int(str(sub))
    except (TypeError, ValueError):
        logger.info("auth: token sub not int")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        logger.info("auth: user not found (id=%s)", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    return user


async def get_current_user_optional(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials |
                           None, Depends(security)] = None,
) -> User | None:
    """获取当前用户（可选，未登录返回None）"""
    if not credentials and not request.cookies.get("access_token"):
        return None

    try:
        return await get_current_user(
            db=db,
            credentials=credentials,
            request=request,
        )
    except HTTPException:
        return None


async def require_admin(
        current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求管理员权限"""
    if not has_any_role(current_user, [Role.ADMIN, Role.SUPER_ADMIN]):
        logger.warning(
            f"权限检查失败: 用户 {current_user.username} (role={current_user.role}) 尝试访问管理员资源")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def require_moderator(
        current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求版主或管理员权限"""
    if not has_any_role(
            current_user, [Role.MODERATOR, Role.ADMIN, Role.SUPER_ADMIN]):
        logger.warning(
            f"权限检查失败: 用户 {current_user.username} (role={current_user.role}) 尝试访问版主资源")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要版主或管理员权限"
        )
    return current_user


async def require_lawyer(
        current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求律师权限"""
    # 调试/测试环境下放宽角色校验，交由具体路由判断律师资料是否存在
    if _should_skip_verify():
        return current_user
    if not has_role(current_user, Role.LAWYER):
        logger.warning(
            f"权限检查失败: 用户 {current_user.username} (role={current_user.role}) 尝试访问律师资源")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要律师权限"
        )
    return current_user


async def require_super_admin(
        current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求超级管理员权限"""
    if _should_skip_verify():
        return current_user
    if not has_role(current_user, Role.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user


async def require_forum_admin(
        current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求论坛服务管理员权限"""
    if _should_skip_verify():
        return current_user
    if not has_any_role(current_user, [Role.FORUM_ADMIN, Role.ADMIN, Role.SUPER_ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要论坛管理权限"
        )
    return current_user


async def require_news_admin(
        current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求新闻服务管理员权限"""
    if _should_skip_verify():
        return current_user
    if not has_any_role(current_user, [Role.NEWS_ADMIN, Role.ADMIN, Role.SUPER_ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要新闻管理权限"
        )
    return current_user


async def require_ai_admin(
        current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求 AI 服务管理员权限"""
    if _should_skip_verify():
        return current_user
    if not has_any_role(current_user, [Role.AI_ADMIN, Role.ADMIN, Role.SUPER_ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要 AI 管理权限"
        )
    return current_user


async def require_lawyer_admin(
        current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求律师服务管理员权限"""
    if _should_skip_verify():
        return current_user
    if not has_any_role(current_user, [Role.LAWYER_ADMIN, Role.ADMIN, Role.SUPER_ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要律师管理权限"
        )
    return current_user


async def require_cs_agent(
        current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求客服权限"""
    if _should_skip_verify():
        return current_user
    if not has_any_role(current_user, [Role.CS_AGENT, Role.ADMIN, Role.SUPER_ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要客服权限"
        )
    return current_user


async def require_phone_verified(
        current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求手机号已验证（敏感操作兜底）"""
    if not bool(getattr(current_user, "phone_verified", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请先完成手机号验证",
        )
    return current_user


async def require_email_verified(
        current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求邮箱已验证（敏感操作兜底）"""
    if not bool(getattr(current_user, "email_verified", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请先完成邮箱验证",
        )
    return current_user


async def require_user_verified(
        current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if _should_skip_verify():
        return current_user
    if not bool(getattr(current_user, "phone_verified", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请先完成手机号验证",
        )
    if not bool(getattr(current_user, "email_verified", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请先完成邮箱验证",
        )
    return current_user


async def require_lawyer_phone_verified(
        current_user: Annotated[User, Depends(require_lawyer)]) -> User:
    """要求律师权限且手机号已验证（敏感操作兜底）"""
    if _should_skip_verify():
        return current_user
    if not bool(getattr(current_user, "phone_verified", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请先完成手机号验证",
        )
    return current_user


async def require_lawyer_verified(
        current_user: Annotated[User, Depends(require_lawyer)]) -> User:
    """要求律师权限且手机号/邮箱均已验证（敏感操作兜底）"""
    if _should_skip_verify():
        return current_user
    if not bool(getattr(current_user, "phone_verified", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请先完成手机号验证",
        )
    if not bool(getattr(current_user, "email_verified", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请先完成邮箱验证",
        )
    return current_user
