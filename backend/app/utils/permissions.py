"""权限验证装饰器"""
import logging
from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, status

from ..models.user import User

logger = logging.getLogger(__name__)


class Permission:
    """权限常量"""
    # 用户权限
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"

    # 帖子权限
    POST_READ = "post:read"
    POST_WRITE = "post:write"
    POST_DELETE = "post:delete"
    POST_MANAGE = "post:manage"

    # 评论权限
    COMMENT_READ = "comment:read"
    COMMENT_WRITE = "comment:write"
    COMMENT_DELETE = "comment:delete"

    # 新闻权限
    NEWS_READ = "news:read"
    NEWS_WRITE = "news:write"
    NEWS_DELETE = "news:delete"
    NEWS_MANAGE = "news:manage"

    # 知识库权限
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"
    KNOWLEDGE_DELETE = "knowledge:delete"

    # 论坛管理权限
    FORUM_READ = "forum:read"
    FORUM_MODERATE = "forum:moderate"
    FORUM_MANAGE = "forum:manage"

    # AI 服务权限
    AI_CONFIG = "ai:config"
    AI_MONITOR = "ai:monitor"
    AI_TEMPLATES = "ai:templates"

    # 律师服务权限
    LAWYER_VERIFY = "lawyer:verify"
    LAWYER_FIRM = "lawyer:firm"
    LAWYER_CASES = "lawyer:cases"
    LAWYER_DOCUMENTS = "lawyer:documents"

    # 客服权限
    CS_TICKETS = "cs:tickets"
    CS_FEEDBACK = "cs:feedback"

    # 管理员权限
    ADMIN_ACCESS = "admin:access"
    ADMIN_USERS = "admin:users"
    ADMIN_CONTENT = "admin:content"
    ADMIN_SYSTEM = "admin:system"


class Role:
    """角色常量"""
    USER = "user"
    LAWYER = "lawyer"
    MODERATOR = "moderator"
    FORUM_ADMIN = "forum_admin"
    NEWS_ADMIN = "news_admin"
    AI_ADMIN = "ai_admin"
    LAWYER_ADMIN = "lawyer_admin"
    CS_AGENT = "cs_agent"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


ROLE_LABELS: dict[str, str] = {
    Role.USER: "普通用户",
    Role.LAWYER: "律师",
    Role.MODERATOR: "审核员",
    Role.FORUM_ADMIN: "论坛服务管理员",
    Role.NEWS_ADMIN: "新闻服务管理员",
    Role.AI_ADMIN: "AI 服务管理员",
    Role.LAWYER_ADMIN: "律师服务管理员",
    Role.CS_AGENT: "客服",
    Role.ADMIN: "管理员",
    Role.SUPER_ADMIN: "超级管理员",
}


ROLE_DASHBOARD_MAP: dict[str, str] = {
    Role.SUPER_ADMIN: "/admin/super",
    Role.ADMIN: "/admin/general",
    Role.FORUM_ADMIN: "/admin/forum",
    Role.NEWS_ADMIN: "/admin/news",
    Role.AI_ADMIN: "/admin/ai",
    Role.LAWYER_ADMIN: "/admin/lawyer",
    Role.CS_AGENT: "/admin/cs",
}


ROLE_ADMIN_HIERARCHY: dict[str, str | None] = {
    Role.SUPER_ADMIN: None,
    Role.ADMIN: Role.SUPER_ADMIN,
    Role.FORUM_ADMIN: Role.SUPER_ADMIN,
    Role.NEWS_ADMIN: Role.SUPER_ADMIN,
    Role.AI_ADMIN: Role.SUPER_ADMIN,
    Role.LAWYER_ADMIN: Role.SUPER_ADMIN,
    Role.CS_AGENT: Role.SUPER_ADMIN,
    Role.MODERATOR: Role.FORUM_ADMIN,
}


# 角色权限映射
ROLE_PERMISSIONS: dict[str, set[str]] = {
    Role.USER: {
        Permission.USER_READ,
        Permission.POST_READ,
        Permission.POST_WRITE,
        Permission.COMMENT_READ,
        Permission.COMMENT_WRITE,
        Permission.NEWS_READ,
        Permission.KNOWLEDGE_READ,
    },
    Role.LAWYER: {
        Permission.USER_READ,
        Permission.POST_READ,
        Permission.POST_WRITE,
        Permission.COMMENT_READ,
        Permission.COMMENT_WRITE,
        Permission.NEWS_READ,
        Permission.KNOWLEDGE_READ,
        Permission.KNOWLEDGE_WRITE,
    },
    Role.MODERATOR: {
        Permission.USER_READ,
        Permission.POST_READ,
        Permission.POST_WRITE,
        Permission.POST_DELETE,
        Permission.POST_MANAGE,
        Permission.COMMENT_READ,
        Permission.COMMENT_WRITE,
        Permission.COMMENT_DELETE,
        Permission.NEWS_READ,
        Permission.KNOWLEDGE_READ,
        Permission.FORUM_READ,
        Permission.FORUM_MODERATE,
        Permission.ADMIN_CONTENT,
    },
    Role.FORUM_ADMIN: {
        Permission.USER_READ,
        Permission.POST_READ,
        Permission.POST_WRITE,
        Permission.POST_DELETE,
        Permission.POST_MANAGE,
        Permission.COMMENT_READ,
        Permission.COMMENT_WRITE,
        Permission.COMMENT_DELETE,
        Permission.NEWS_READ,
        Permission.KNOWLEDGE_READ,
        Permission.FORUM_READ,
        Permission.FORUM_MODERATE,
        Permission.FORUM_MANAGE,
        Permission.ADMIN_ACCESS,
        Permission.ADMIN_CONTENT,
    },
    Role.NEWS_ADMIN: {
        Permission.USER_READ,
        Permission.POST_READ,
        Permission.COMMENT_READ,
        Permission.NEWS_READ,
        Permission.NEWS_WRITE,
        Permission.NEWS_DELETE,
        Permission.NEWS_MANAGE,
        Permission.KNOWLEDGE_READ,
        Permission.ADMIN_ACCESS,
        Permission.ADMIN_CONTENT,
    },
    Role.AI_ADMIN: {
        Permission.USER_READ,
        Permission.POST_READ,
        Permission.COMMENT_READ,
        Permission.NEWS_READ,
        Permission.KNOWLEDGE_READ,
        Permission.AI_CONFIG,
        Permission.AI_MONITOR,
        Permission.AI_TEMPLATES,
        Permission.ADMIN_ACCESS,
    },
    Role.LAWYER_ADMIN: {
        Permission.USER_READ,
        Permission.POST_READ,
        Permission.COMMENT_READ,
        Permission.NEWS_READ,
        Permission.KNOWLEDGE_READ,
        Permission.LAWYER_VERIFY,
        Permission.LAWYER_FIRM,
        Permission.LAWYER_CASES,
        Permission.LAWYER_DOCUMENTS,
        Permission.ADMIN_ACCESS,
    },
    Role.CS_AGENT: {
        Permission.USER_READ,
        Permission.POST_READ,
        Permission.COMMENT_READ,
        Permission.NEWS_READ,
        Permission.KNOWLEDGE_READ,
        Permission.CS_TICKETS,
        Permission.CS_FEEDBACK,
        Permission.ADMIN_ACCESS,
    },
    Role.ADMIN: {
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.POST_READ,
        Permission.POST_WRITE,
        Permission.POST_DELETE,
        Permission.POST_MANAGE,
        Permission.COMMENT_READ,
        Permission.COMMENT_WRITE,
        Permission.COMMENT_DELETE,
        Permission.NEWS_READ,
        Permission.NEWS_WRITE,
        Permission.NEWS_DELETE,
        Permission.KNOWLEDGE_READ,
        Permission.KNOWLEDGE_WRITE,
        Permission.KNOWLEDGE_DELETE,
        Permission.FORUM_READ,
        Permission.FORUM_MODERATE,
        Permission.ADMIN_ACCESS,
        Permission.ADMIN_USERS,
        Permission.ADMIN_CONTENT,
    },
    Role.SUPER_ADMIN: {
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.USER_DELETE,
        Permission.POST_READ,
        Permission.POST_WRITE,
        Permission.POST_DELETE,
        Permission.POST_MANAGE,
        Permission.COMMENT_READ,
        Permission.COMMENT_WRITE,
        Permission.COMMENT_DELETE,
        Permission.NEWS_READ,
        Permission.NEWS_WRITE,
        Permission.NEWS_DELETE,
        Permission.NEWS_MANAGE,
        Permission.KNOWLEDGE_READ,
        Permission.KNOWLEDGE_WRITE,
        Permission.KNOWLEDGE_DELETE,
        Permission.FORUM_READ,
        Permission.FORUM_MODERATE,
        Permission.FORUM_MANAGE,
        Permission.AI_CONFIG,
        Permission.AI_MONITOR,
        Permission.AI_TEMPLATES,
        Permission.LAWYER_VERIFY,
        Permission.LAWYER_FIRM,
        Permission.LAWYER_CASES,
        Permission.LAWYER_DOCUMENTS,
        Permission.CS_TICKETS,
        Permission.CS_FEEDBACK,
        Permission.ADMIN_ACCESS,
        Permission.ADMIN_USERS,
        Permission.ADMIN_CONTENT,
        Permission.ADMIN_SYSTEM,
    },
}


def has_permission(user: User, permission: str) -> bool:
    """
    检查用户是否拥有指定权限

    Args:
        user: 用户对象
        permission: 权限字符串

    Returns:
        是否拥有权限
    """
    if not user:
        return False

    # 获取用户角色的权限集合
    user_permissions = ROLE_PERMISSIONS.get(user.role, set())

    return permission in user_permissions


def has_role(user: User, role: str) -> bool:
    """
    检查用户是否拥有指定角色

    Args:
        user: 用户对象
        role: 角色字符串

    Returns:
        是否拥有角色
    """
    if not user:
        return False

    return user.role == role


def has_any_role(user: User, roles: list[str]) -> bool:
    """
    检查用户是否拥有任一指定角色

    Args:
        user: 用户对象
        roles: 角色列表

    Returns:
        是否拥有任一角色
    """
    if not user:
        return False

    return user.role in roles


def require_permission(permission: str):
    """
    权限验证装饰器

    用法:
        @require_permission(Permission.POST_DELETE)
        async def delete_post(post_id: int, current_user: User = Depends(get_current_user)):
            ...

    Args:
        permission: 所需权限
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 从参数中获取 current_user
            current_user = kwargs.get('current_user')

            if not current_user:
                logger.warning("权限检查失败: 未找到 current_user 参数")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证"
                )

            if not has_permission(current_user, permission):
                logger.warning(
                    f"权限检查失败: 用户 {current_user.username} (role={current_user.role}) "
                    f"尝试访问需要 {permission} 权限的资源"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要权限: {permission}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_role(role: str):
    """
    角色验证装饰器

    用法:
        @require_role(Role.ADMIN)
        async def admin_function(current_user: User = Depends(get_current_user)):
            ...

    Args:
        role: 所需角色
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_user = kwargs.get('current_user')

            if not current_user:
                logger.warning("角色检查失败: 未找到 current_user 参数")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证"
                )

            if not has_role(current_user, role):
                logger.warning(
                    f"角色检查失败: 用户 {current_user.username} (role={current_user.role}) "
                    f"尝试访问需要 {role} 角色的资源"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要角色: {role}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_any_role(roles: list[str]):
    """
    多角色验证装饰器（满足任一角色即可）

    用法:
        @require_any_role([Role.ADMIN, Role.MODERATOR])
        async def moderate_content(current_user: User = Depends(get_current_user)):
            ...

    Args:
        roles: 角色列表
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_user = kwargs.get('current_user')

            if not current_user:
                logger.warning("角色检查失败: 未找到 current_user 参数")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证"
                )

            if not has_any_role(current_user, roles):
                logger.warning(
                    f"角色检查失败: 用户 {current_user.username} (role={current_user.role}) "
                    f"尝试访问需要 {roles} 任一角色的资源"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要以下任一角色: {', '.join(roles)}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def is_owner_or_admin(user: User, resource_user_id: int) -> bool:
    """
    检查用户是否是资源所有者或管理员

    Args:
        user: 当前用户
        resource_user_id: 资源所有者ID

    Returns:
        是否有权限
    """
    if not user:
        return False

    # 是资源所有者
    if user.id == resource_user_id:
        return True

    # 是管理员或版主
    if user.role in [Role.ADMIN, Role.SUPER_ADMIN, Role.MODERATOR]:
        return True

    return False


def require_owner_or_admin(resource_user_id_key: str = "user_id"):
    """
    所有者或管理员验证装饰器

    用法:
        @require_owner_or_admin("post.user_id")
        async def update_post(post: Post, current_user: User = Depends(get_current_user)):
            ...

    Args:
        resource_user_id_key: 资源所有者ID的键名（支持点号访问嵌套属性）
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_user = kwargs.get('current_user')

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证"
                )

            # 获取资源所有者ID
            resource_user_id = None
            keys = resource_user_id_key.split('.')

            # 尝试从kwargs中获取
            obj = kwargs.get(keys[0])
            if obj:
                for key in keys[1:]:
                    obj = getattr(obj, key, None)
                    if obj is None:
                        break
                resource_user_id = obj

            if resource_user_id is None:
                logger.error(f"无法获取资源所有者ID: {resource_user_id_key}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="权限验证失败"
                )

            if not is_owner_or_admin(current_user, resource_user_id):
                logger.warning(
                    f"权限检查失败: 用户 {current_user.username} "
                    f"尝试访问用户 {resource_user_id} 的资源"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有资源所有者或管理员可以执行此操作"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
