"""积分系统数据库模型"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from ..database import Base


class PointsUser(Base):
    """用户积分账户"""
    __tablename__ = "points_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True)
    balance = Column(Integer, default=0, nullable=False)
    total_earned = Column(Integer, default=0, nullable=False)
    total_spent = Column(Integer, default=0, nullable=False)
    continuous_signin_days = Column(Integer, default=0, nullable=False)
    last_signin_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    history = relationship(
        "PointsHistory",
        back_populates="user",
        cascade="all, delete-orphan")
    daily_counts = relationship(
        "PointsDailyCount",
        back_populates="user",
        cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PointsUser user_id={self.user_id} balance={self.balance}>"


class PointsHistory(Base):
    """积分变动历史"""
    __tablename__ = "points_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("points_users.user_id"),
        nullable=False,
        index=True)
    action = Column(String(50), nullable=False, index=True)
    points = Column(Integer, nullable=False)
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    user = relationship("PointsUser", back_populates="history")

    def __repr__(self):
        return f"<PointsHistory user_id={self.user_id} action={self.action} points={self.points}>"


class PointsDailyCount(Base):
    """每日积分动作计数"""
    __tablename__ = "points_daily_counts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("points_users.user_id"),
        nullable=False,
        index=True)
    action = Column(String(50), nullable=False)
    count = Column(Integer, default=0, nullable=False)
    date = Column(String(10), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("PointsUser", back_populates="daily_counts")

    __table_args__ = (
        Index('ix_points_daily_counts_user_date', 'user_id', 'date'),
    )

    def __repr__(self):
        return f"<PointsDailyCount user_id={self.user_id} action={self.action} date={self.date}>"


class Product(Base):
    """积分商品（测试兼容模型）"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    category = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class PointsProduct(Base):
    """积分商品"""
    __tablename__ = "points_products"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    points_required = Column(Integer, nullable=False)
    product_type = Column(String(50), nullable=False, index=True)
    image_url = Column(String(500), nullable=True)
    stock = Column(Integer, default=-1, nullable=False)  # -1 表示无限
    status = Column(String(20), default="active", nullable=False)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    orders = relationship(
        "PointsExchangeOrder",
        back_populates="product",
        cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PointsProduct id={self.id} name={self.name} points={self.points_required}>"


class PointsExchangeOrder(Base):
    """积分兑换订单"""
    __tablename__ = "points_exchange_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True)
    product_id = Column(
        String(50),
        ForeignKey("points_products.id"),
        nullable=False,
        index=True)
    product_name = Column(String(100), nullable=False)
    points_spent = Column(Integer, nullable=False)
    # pending, completed, cancelled
    status = Column(String(20), default="pending", nullable=False)
    shipping_info = Column(JSON, nullable=True)
    remark = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    product = relationship("PointsProduct", back_populates="orders")

    def __repr__(self):
        return f"<PointsExchangeOrder id={self.id} order_no={self.order_no} status={self.status}>"
