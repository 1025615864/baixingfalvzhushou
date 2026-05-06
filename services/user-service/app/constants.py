"""常量定义"""

ROLE_HIERARCHY = {
    "admin": 3,
    "vip": 2,
    "user": 1,
}


def get_role_level(role: str) -> int:
    """获取角色等级"""
    return ROLE_HIERARCHY.get(role, 0)


def has_permission(user_role: str, required_role: str) -> bool:
    """检查用户是否有足够权限"""
    return get_role_level(user_role) >= get_role_level(required_role)
