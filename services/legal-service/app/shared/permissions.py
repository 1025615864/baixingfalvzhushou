"""声明式权限系统"""
from enum import Enum
from typing import Set


class Permission(str, Enum):
    """细粒度权限定义"""

    CONSULTATION_CREATE = "consultation:create"
    CONSULTATION_READ = "consultation:read"
    CONSULTATION_REPLY = "consultation:reply"
    CONSULTATION_ASSIGN = "consultation:assign"
    CONSULTATION_CANCEL = "consultation:cancel"
    CONSULTATION_COMPLETE = "consultation:complete"

    LAWYER_READ = "lawyer:read"
    LAWYER_CREATE = "lawyer:create"
    LAWYER_UPDATE = "lawyer:update"
    LAWYER_VERIFY = "lawyer:verify"
    LAWYER_REJECT = "lawyer:reject"

    FIRM_CREATE = "firm:create"
    FIRM_READ = "firm:read"
    FIRM_UPDATE = "firm:update"
    FIRM_MANAGE_OWN = "firm:manage_own"
    FIRM_MANAGE_ALL = "firm:manage_all"
    FIRM_APPROVE = "firm:approve"
    FIRM_INVITE = "firm:invite"
    FIRM_REMOVE_LAWYER = "firm:remove_lawyer"

    APPOINTMENT_CREATE = "appointment:create"
    APPOINTMENT_READ = "appointment:read"
    APPOINTMENT_CANCEL = "appointment:cancel"
    APPOINTMENT_MANAGE = "appointment:manage"

    DOCUMENT_CREATE = "document:create"
    DOCUMENT_READ = "document:read"
    DOCUMENT_UPDATE = "document:update"

    REVIEW_CREATE = "review:create"
    REVIEW_READ = "review:read"

    ADMIN_STATS = "admin:stats"
    ADMIN_CACHE = "admin:cache"
    ADMIN_METRICS = "admin:metrics"
    ADMIN_FIRM_ALL = "admin:firm_all"
    ADMIN_LAWYER_ALL = "admin:lawyer_all"
    ADMIN_CONSULTATION_ALL = "admin:consultation_all"


ROLE_PERMISSIONS: dict[str, Set[Permission]] = {
    "user": {
        Permission.CONSULTATION_CREATE,
        Permission.CONSULTATION_READ,
        Permission.LAWYER_READ,
        Permission.FIRM_READ,
        Permission.APPOINTMENT_CREATE,
        Permission.APPOINTMENT_READ,
        Permission.DOCUMENT_READ,
        Permission.REVIEW_CREATE,
        Permission.REVIEW_READ,
    },
    "lawyer": {
        Permission.CONSULTATION_CREATE,
        Permission.CONSULTATION_READ,
        Permission.CONSULTATION_REPLY,
        Permission.LAWYER_READ,
        Permission.LAWYER_UPDATE,
        Permission.FIRM_READ,
        Permission.APPOINTMENT_CREATE,
        Permission.APPOINTMENT_READ,
        Permission.APPOINTMENT_CANCEL,
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.REVIEW_READ,
    },
    "lawfirm_admin": {
        Permission.CONSULTATION_READ,
        Permission.CONSULTATION_ASSIGN,
        Permission.LAWYER_READ,
        Permission.FIRM_READ,
        Permission.FIRM_MANAGE_OWN,
        Permission.FIRM_INVITE,
        Permission.FIRM_REMOVE_LAWYER,
        Permission.APPOINTMENT_READ,
        Permission.APPOINTMENT_MANAGE,
        Permission.DOCUMENT_READ,
        Permission.REVIEW_READ,
    },
    "platform_firm_admin": {
        Permission.FIRM_READ,
        Permission.FIRM_MANAGE_ALL,
        Permission.FIRM_APPROVE,
        Permission.FIRM_INVITE,
        Permission.ADMIN_FIRM_ALL,
        Permission.ADMIN_STATS,
    },
    "admin": {
        Permission.CONSULTATION_CREATE,
        Permission.CONSULTATION_READ,
        Permission.CONSULTATION_REPLY,
        Permission.CONSULTATION_ASSIGN,
        Permission.CONSULTATION_CANCEL,
        Permission.CONSULTATION_COMPLETE,
        Permission.LAWYER_READ,
        Permission.LAWYER_CREATE,
        Permission.LAWYER_UPDATE,
        Permission.LAWYER_VERIFY,
        Permission.LAWYER_REJECT,
        Permission.FIRM_CREATE,
        Permission.FIRM_READ,
        Permission.FIRM_UPDATE,
        Permission.FIRM_MANAGE_OWN,
        Permission.FIRM_MANAGE_ALL,
        Permission.FIRM_APPROVE,
        Permission.FIRM_INVITE,
        Permission.FIRM_REMOVE_LAWYER,
        Permission.APPOINTMENT_CREATE,
        Permission.APPOINTMENT_READ,
        Permission.APPOINTMENT_CANCEL,
        Permission.APPOINTMENT_MANAGE,
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE,
        Permission.REVIEW_CREATE,
        Permission.REVIEW_READ,
        Permission.ADMIN_STATS,
        Permission.ADMIN_CACHE,
        Permission.ADMIN_METRICS,
        Permission.ADMIN_FIRM_ALL,
        Permission.ADMIN_LAWYER_ALL,
        Permission.ADMIN_CONSULTATION_ALL,
    },
}


def get_permissions_for_role(role: str) -> Set[Permission]:
    """获取角色对应的权限集合"""
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: str, permission: Permission) -> bool:
    """检查角色是否拥有特定权限"""
    return permission in ROLE_PERMISSIONS.get(role, set())