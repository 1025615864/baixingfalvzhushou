"""法律文书商城数据库模型

存储法律文书商城的商品、分类、订单等数据。
支持积分购买和会员权益。
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .user import User


class LegalDocumentCategory(str, enum.Enum):
    """法律文书分类"""

    # 合同范本
    CONTRACT_RENTAL = "contract_rental"  # 租赁合同
    CONTRACT_PURCHASE = "contract_purchase"  # 买卖合同
    CONTRACT_LABOR = "contract_labor"  # 劳动合同
    CONTRACT_MARRIAGE = "contract_marriage"  # 婚姻家庭
    CONTRACT_ENTERPRISE = "contract_enterprise"  # 企业合同

    # 法律文书
    LEGAL_PETITION = "legal_petition"  # 起诉状
    LEGAL_ANSWER = "legal_answer"  # 答辩状
    LEGAL_APPLICATION = "legal_application"  # 申请书
    LEGAL_AGREEMENT = "legal_agreement"  # 协议

    # 企业文书
    ENTERPRISE_CHARTER = "enterprise_charter"  # 公司章程
    ENTERPRISE_LABOR = "enterprise_labor"  # 企业劳动合同模板
    ENTERPRISE_INTERNAL = "enterprise_internal"  # 内部管理制度


class LegalDocument(Base):
    """法律文书商品"""

    __tablename__: str = "legal_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 基本信息
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 文书内容
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # 价格信息
    price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 价格（积分）
    points_required: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 所需积分

    # 会员价格（JSON格式存储）
    member_prices: Mapped[str | None] = mapped_column(
        "member_prices_json", JSON, nullable=True
    )  # {"annual": 80, "lifetime": 50}

    # 状态和统计
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否免费
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否推荐
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Integer, default=0)  # 评分（1-5）

    # 扩展信息
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 标签，逗号分隔
    extra_data: Mapped[str | None] = mapped_column(JSON, nullable=True)  # 扩展数据

    # 律师定制服务
    custom_service_available: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # 是否支持定制
    custom_service_price: Mapped[int] = mapped_column(Integer, default=0)  # 定制服务价格

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # 关联
    orders = relationship(
        "LegalDocumentOrder",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_legal_documents_category_active", "category", "is_active"),
        Index("ix_legal_documents_featured", "is_featured", "is_active"),
    )


class LegalDocumentOrder(Base):
    """法律文书购买/下载记录"""

    __tablename__: str = "legal_document_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )

    # 用户信息
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # 文书信息
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("legal_documents.id"), nullable=False, index=True
    )

    # 购买信息
    points_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 消耗积分
    original_points: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # 原价积分
    discount_amount: Mapped[int] = mapped_column(Integer, default=0)  # 优惠金额

    # 支付方式
    payment_method: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # points, money, member_free

    # 订单状态
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )  # pending, completed, cancelled, refunded

    # 备注
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 时间戳
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # 关联
    user: Mapped["User"] = relationship("User", back_populates=None)
    document: Mapped["LegalDocument"] = relationship(
        "LegalDocument", back_populates="orders"
    )

    __table_args__ = (
        Index("ix_legal_document_orders_user", "user_id", "status"),
        Index("ix_legal_document_orders_document", "document_id"),
    )


class LegalDocumentFavorite(Base):
    """法律文书收藏"""

    __tablename__: str = "legal_document_favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("legal_documents.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "document_id", name="uq_user_document_favorite"),
    )