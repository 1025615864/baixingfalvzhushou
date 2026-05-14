"""RBAC 角色权限模型 - 支持业务域隔离的并行角色体系

角色体系设计：
- 全局角色：super_admin, admin（跨域管理）
- 业务域角色：每个业务域有独立的管理员和运营角色
  - legal: 律师服务管理员(律所审核), 律师服务运营(律师审核), 律所法人
  - news: 新闻管理员, 新闻运营
  - community: 论坛管理员, 论坛运营, 论坛客服
  - order: 订单管理员, 订单运营
  - payment: 支付管理员, 财务运营
  - knowledge: 知识管理员, 知识运营
  - archive: 档案管理员, 档案运营
  - notification: 通知管理员, 通知运营
  - embedding: 嵌入服务管理员
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Text, JSON, ForeignKey, Table, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

BUSINESS_DOMAINS = {
    "global": "全局",
    "legal": "律师服务",
    "news": "新闻服务",
    "community": "社区论坛",
    "order": "订单服务",
    "payment": "支付服务",
    "knowledge": "知识服务",
    "archive": "档案服务",
    "notification": "通知服务",
    "embedding": "嵌入服务",
}

PRESET_ROLES = [
    {"code": "super_admin", "name": "超级管理员", "domain": "global", "is_system": True,
     "description": "系统最高权限，管理所有业务域"},
    {"code": "admin", "name": "系统管理员", "domain": "global", "is_system": True,
     "description": "系统级管理，跨域配置"},

    {"code": "legal_admin", "name": "律师服务管理员", "domain": "legal", "is_system": True,
     "description": "管理律所审核、律所入驻审批"},
    {"code": "legal_ops", "name": "律师服务运营", "domain": "legal", "is_system": True,
     "description": "管理律师审核、律师认证审核"},
    {"code": "lawfirm_owner", "name": "律所法人", "domain": "legal", "is_system": True,
     "description": "律所法人，管理本律所律师和运营"},

    {"code": "news_admin", "name": "新闻管理员", "domain": "news", "is_system": True,
     "description": "管理新闻审核、发布策略"},
    {"code": "news_ops", "name": "新闻运营", "domain": "news", "is_system": True,
     "description": "新闻内容编辑、发布操作"},

    {"code": "community_admin", "name": "论坛管理员", "domain": "community", "is_system": True,
     "description": "管理论坛审核策略、用户管理"},
    {"code": "community_ops", "name": "论坛运营", "domain": "community", "is_system": True,
     "description": "帖子审核、内容管理"},
    {"code": "community_cs", "name": "论坛客服", "domain": "community", "is_system": True,
     "description": "用户咨询处理、投诉处理"},

    {"code": "order_admin", "name": "订单管理员", "domain": "order", "is_system": True,
     "description": "管理订单、退款审核"},
    {"code": "order_ops", "name": "订单运营", "domain": "order", "is_system": True,
     "description": "订单处理、异常处理"},

    {"code": "payment_admin", "name": "支付管理员", "domain": "payment", "is_system": True,
     "description": "管理支付渠道、风控配置"},
    {"code": "payment_ops", "name": "财务运营", "domain": "payment", "is_system": True,
     "description": "结算管理、对账处理"},

    {"code": "knowledge_admin", "name": "知识管理员", "domain": "knowledge", "is_system": True,
     "description": "管理知识审核、分类管理"},
    {"code": "knowledge_ops", "name": "知识运营", "domain": "knowledge", "is_system": True,
     "description": "知识内容编辑、质量评分"},

    {"code": "archive_admin", "name": "档案管理员", "domain": "archive", "is_system": True,
     "description": "管理案例审核、数据治理"},
    {"code": "archive_ops", "name": "档案运营", "domain": "archive", "is_system": True,
     "description": "案例内容编辑、分类管理"},

    {"code": "notification_admin", "name": "通知管理员", "domain": "notification", "is_system": True,
     "description": "管理通知模板、推送策略"},
    {"code": "notification_ops", "name": "通知运营", "domain": "notification", "is_system": True,
     "description": "通知发送、批量推送"},

    {"code": "embedding_admin", "name": "嵌入服务管理员", "domain": "embedding", "is_system": True,
     "description": "管理嵌入模型、配额配置"},
]

DOMAIN_ROLE_HIERARCHY = {
    "global": {
        "super_admin": ["admin"],
        "admin": [],
    },
    "legal": {
        "legal_admin": ["legal_ops", "lawfirm_owner"],
        "legal_ops": [],
        "lawfirm_owner": [],
    },
    "news": {
        "news_admin": ["news_ops"],
        "news_ops": [],
    },
    "community": {
        "community_admin": ["community_ops", "community_cs"],
        "community_ops": [],
        "community_cs": [],
    },
    "order": {
        "order_admin": ["order_ops"],
        "order_ops": [],
    },
    "payment": {
        "payment_admin": ["payment_ops"],
        "payment_ops": [],
    },
    "knowledge": {
        "knowledge_admin": ["knowledge_ops"],
        "knowledge_ops": [],
    },
    "archive": {
        "archive_admin": ["archive_ops"],
        "archive_ops": [],
    },
    "notification": {
        "notification_admin": ["notification_ops"],
        "notification_ops": [],
    },
    "embedding": {
        "embedding_admin": [],
    },
}


user_roles = Table(
    "user_roles",
    Base.metadata,
    mapped_column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    mapped_column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    mapped_column("scope_id", Integer, nullable=True),
    mapped_column("created_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    mapped_column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    mapped_column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    mapped_column("created_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)


class Role(Base):
    """角色表 - 支持业务域隔离"""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    domain: Mapped[str] = mapped_column(String(30), nullable=False, default="global", index=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions, back_populates="roles", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_role_domain_code", "domain", "code"),
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, code={self.code}, domain={self.domain})>"


class Permission(Base):
    """权限表"""
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    domain: Mapped[str] = mapped_column(String(30), nullable=False, default="global", index=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        secondary=role_permissions, back_populates="permissions", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_permission_resource_action", "resource", "action"),
        Index("ix_permission_domain", "domain"),
    )

    def __repr__(self) -> str:
        return f"<Permission(code={self.code}, domain={self.domain})>"


class UserAuditLog(Base):
    """用户审计日志表"""
    __tablename__ = "user_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    operator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    operator_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    __table_args__ = (
        Index("ix_user_audit_user_action", "user_id", "action"),
    )

    def __repr__(self) -> str:
        return f"<UserAuditLog(id={self.id}, user_id={self.user_id}, action={self.action})>"
