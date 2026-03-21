"""用户画像模型"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class UserProfile(Base):
    """用户画像表"""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)

    # 兴趣标签（JSON数组）
    interest_tags = Column(JSON, default=list)

    # 兴趣权重（JSON对象）
    interest_weights = Column(JSON, default=dict)

    # 偏好的内容类型
    preferred_content_types = Column(JSON, default=list)

    # 使用频率
    # often, sometimes, rarely
    usage_frequency = Column(String(20), default="unknown")

    # 引导完成状态
    onboarding_completed = Column(Boolean, default=False)
    onboarding_completed_at = Column(DateTime, nullable=True)

    # 位置信息
    location = Column(String(100), nullable=True)

    # 预算范围
    budget_range = Column(String(20), nullable=True)

    # 经验水平
    # novice, basic, experienced
    experience_level = Column(String(20), nullable=True)

    # 扩展属性
    extra_data = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<UserProfile user_id={self.user_id} onboarding={self.onboarding_completed}>"


class UserInterestHistory(Base):
    """用户兴趣历史记录（用于追踪兴趣变化）"""
    __tablename__ = "user_interest_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)

    # 行为类型
    # chat, document, lawyer, news, forum, tool
    behavior_type = Column(String(50), nullable=False)

    # 内容标签
    content_tags = Column(JSON, default=list)

    # 交互类型
    # viewed, liked, searched, generated
    interaction_type = Column(String(50), default="viewed")

    # 交互权重
    weight = Column(Float, default=1.0)

    # 交互的内容ID
    content_id = Column(String(100), nullable=True)
    content_type = Column(String(50), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<UserInterestHistory user_id={self.user_id} behavior={self.behavior_type}>"


class UserTagInteraction(Base):
    """用户与标签的交互统计"""
    __tablename__ = "user_tag_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)

    # 标签
    tag = Column(String(100), nullable=False, index=True)

    # 交互次数
    interaction_count = Column(Integer, default=0)

    # 最后交互时间
    last_interaction_at = Column(DateTime, nullable=True)

    # 权重累计
    total_weight = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<UserTagInteraction user_id={self.user_id} tag={self.tag} count={self.interaction_count}>"


class UserOnboarding(Base):
    """用户引导状态表"""
    __tablename__ = "user_onboarding"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)

    # 当前步骤 (0: 未开始, 1: 角色选择, 2: 需求匹配, 3: 功能演示, 4: 完成)
    current_step = Column(Integer, default=0)

    # 选择的角色 ID
    role_id = Column(String(50), nullable=True)

    # 角色选择时间
    role_selected_at = Column(DateTime, nullable=True)

    # 匹配的需求 ID 列表 (JSON 数组)
    matched_needs = Column(JSON, default=list)

    # 需求匹配时间
    needs_matched_at = Column(DateTime, nullable=True)

    # 已完成的功能演示 ID 列表 (JSON 数组)
    completed_demos = Column(JSON, default=list)

    # 演示开始时间
    demo_started_at = Column(DateTime, nullable=True)

    # 引导是否完成
    completed = Column(Boolean, default=False)

    # 引导完成时间
    completed_at = Column(DateTime, nullable=True)

    # 扩展属性 (JSON 对象)
    extra_data = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<UserOnboarding user_id={self.user_id} step={self.current_step} completed={self.completed}>"