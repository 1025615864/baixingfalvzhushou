"""法律咨询所模型"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text, DateTime, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, DynamicMapped
from sqlalchemy.sql import func
from ..database import Base

if TYPE_CHECKING:
    from .user import User


class LawFirm(Base):
    """律师事务所表"""
    __tablename__: str = "law_firms"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(50), nullable=True)
    province: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    license_no: Mapped[str | None] = mapped_column(
        String(100), nullable=True)  # 执业许可证号
    specialties: Mapped[str | None] = mapped_column(
        String(500), nullable=True)  # 专业领域，逗号分隔
    rating: Mapped[float] = mapped_column(Float, default=0.0)  # 评分
    review_count: Mapped[int] = mapped_column(Integer, default=0)  # 评价数
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否认证
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    lawyers: DynamicMapped[Lawyer] = relationship(
        "Lawyer", back_populates="firm", lazy="dynamic")


class Lawyer(Base):
    """律师表"""
    __tablename__: str = "lawyers"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True)  # 关联用户
    firm_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("law_firms.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(
        String(50), nullable=True)  # 职称：律师/合伙人/主任
    license_no: Mapped[str | None] = mapped_column(
        String(100), nullable=True)  # 执业证号
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    introduction: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # 个人简介
    specialties: Mapped[str | None] = mapped_column(
        String(500), nullable=True)  # 擅长领域
    experience_years: Mapped[int] = mapped_column(Integer, default=0)  # 从业年限
    case_count: Mapped[int] = mapped_column(Integer, default=0)  # 案件数
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    consultation_fee: Mapped[float] = mapped_column(Float, default=0.0)  # 咨询费用
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    firm: Mapped[LawFirm | None] = relationship(
        "LawFirm", back_populates="lawyers")
    user: Mapped[User | None] = relationship("User", backref="lawyer_profile")


class LawyerVerification(Base):
    """律师认证申请表"""
    __tablename__: str = "lawyer_verifications"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False)
    real_name: Mapped[str] = mapped_column(String(50), nullable=False)  # 真实姓名
    id_card_no: Mapped[str] = mapped_column(String(20), nullable=False)  # 身份证号
    license_no: Mapped[str] = mapped_column(
        String(100), nullable=False)  # 律师执业证号
    firm_name: Mapped[str] = mapped_column(
        String(200), nullable=False)  # 执业律所名称
    id_card_front: Mapped[str | None] = mapped_column(
        String(255), nullable=True)  # 身份证正面照
    id_card_back: Mapped[str | None] = mapped_column(
        String(255), nullable=True)  # 身份证背面照
    license_photo: Mapped[str | None] = mapped_column(
        String(255), nullable=True)  # 执业证照片
    specialties: Mapped[str | None] = mapped_column(
        String(500), nullable=True)  # 擅长领域
    introduction: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # 个人简介
    experience_years: Mapped[int] = mapped_column(Integer, default=0)  # 从业年限
    status: Mapped[str] = mapped_column(
        String(20), default="pending")  # pending/approved/rejected
    reject_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # 驳回原因
    reviewed_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
        backref="lawyer_verifications")
    reviewer: Mapped[User | None] = relationship(
        "User", foreign_keys=[reviewed_by])


class LawyerConsultation(Base):
    """律师咨询预约表"""
    __tablename__: str = "lawyer_consultations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False)
    lawyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lawyers.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)  # 咨询主题
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # 问题描述
    category: Mapped[str | None] = mapped_column(
        String(50), nullable=True)  # 案件类型
    contact_phone: Mapped[str | None] = mapped_column(
        String(50), nullable=True)
    preferred_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)  # 期望时间
    # pending/confirmed/completed/cancelled
    status: Mapped[str] = mapped_column(String(20), default="pending")
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)  # 管理备注
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    user: Mapped[User] = relationship("User", backref="lawyer_consultations")
    lawyer: Mapped[Lawyer] = relationship("Lawyer", backref="client_consultations")


class LawyerConsultationMessage(Base):
    """律师咨询留言表"""
    __tablename__: str = "lawyer_consultation_messages"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        "lawyer_consultations.id"), nullable=False, index=True)
    sender_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True)
    sender_role: Mapped[str] = mapped_column(
        String(20), nullable=False)  # user/lawyer
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    consultation: Mapped[LawyerConsultation] = relationship(
        "LawyerConsultation",
        backref="messages",
        foreign_keys=[consultation_id],
    )
    sender: Mapped[User] = relationship("User", foreign_keys=[sender_user_id])


class LawyerReview(Base):
    """律师评价表"""
    __tablename__: str = "lawyer_reviews"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lawyers.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False)
    consultation_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("lawyer_consultations.id"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5星
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)

    # 多维度评价
    professionalism: Mapped[int | None] = mapped_column(
        Integer, nullable=True)  # 专业性 1-5
    responsiveness: Mapped[int | None] = mapped_column(
        Integer, nullable=True)  # 响应速度 1-5
    attitude: Mapped[int | None] = mapped_column(
        Integer, nullable=True)  # 服务态度 1-5
    tags: Mapped[str | None] = mapped_column(
        String(500), nullable=True)  # 标签，JSON格式

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    # 关系
    lawyer: Mapped[Lawyer] = relationship("Lawyer", backref="reviews")
    user: Mapped[User] = relationship("User", backref="lawyer_reviews")


class LawyerSchedule(Base):
    """律师日程表"""
    __tablename__: str = "lawyer_schedules"
    __table_args__: tuple[UniqueConstraint, ...] = (
        UniqueConstraint(
            "lawyer_id",
            "date",
            "start_time",
            name="uq_lawyer_schedule_time"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lawyers.id"), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        nullable=False,
        index=True)  # 日期
    start_time: Mapped[str] = mapped_column(
        String(10), nullable=False)  # 开始时间 HH:MM
    end_time: Mapped[str] = mapped_column(
        String(10), nullable=False)  # 结束时间 HH:MM
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否可用
    consultation_id: Mapped[int | None] = mapped_column(
        # 关联的咨询ID
        Integer, ForeignKey("lawyer_consultations.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 备注
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    lawyer: Mapped[Lawyer] = relationship("Lawyer", backref="schedules")
    consultation: Mapped[LawyerConsultation | None] = relationship(
        "LawyerConsultation", backref="schedule")


class LawyerReplyTemplate(Base):
    """律师快捷回复模板表"""
    __tablename__: str = "lawyer_reply_templates"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lawyers.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)  # 模板标题
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 模板内容
    category: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True)  # 分类
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True)  # 是否启用
    use_count: Mapped[int] = mapped_column(Integer, default=0)  # 使用次数
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    lawyer: Mapped[Lawyer] = relationship("Lawyer", backref="reply_templates")


class LawyerHomepage(Base):
    """律师主页定制表"""
    __tablename__: str = "lawyer_homepages"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        "lawyers.id"), nullable=False, unique=True, index=True)

    # 主页基本信息
    banner_image: Mapped[str | None] = mapped_column(
        String(255), nullable=True)  # 横幅图片
    profile_image: Mapped[str | None] = mapped_column(
        String(255), nullable=True)  # 个人形象照
    slogan: Mapped[str | None] = mapped_column(
        String(200), nullable=True)  # 个人标语
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)  # 个人简介（富文本）

    # 专业展示
    specialties_display: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # 擅长领域展示（富文本）
    achievements: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # 成就荣誉（富文本）
    education: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # 教育背景（富文本）

    # 服务展示
    service_areas: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # 服务区域（富文本）
    service_hours: Mapped[str | None] = mapped_column(
        String(200), nullable=True)  # 服务时间
    response_time: Mapped[str | None] = mapped_column(
        String(100), nullable=True)  # 响应时间承诺

    # 联系方式
    contact_phone: Mapped[str | None] = mapped_column(
        String(50), nullable=True)  # 联系电话
    contact_email: Mapped[str | None] = mapped_column(
        String(100), nullable=True)  # 联系邮箱
    wechat_qrcode: Mapped[str | None] = mapped_column(
        String(255), nullable=True)  # 微信二维码

    # 社交媒体
    weibo_url: Mapped[str | None] = mapped_column(
        String(255), nullable=True)  # 微博链接
    linkedin_url: Mapped[str | None] = mapped_column(
        String(255), nullable=True)  # LinkedIn链接
    zhihu_url: Mapped[str | None] = mapped_column(
        String(255), nullable=True)  # 知乎链接

    # 案例展示
    case_studies: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # 案例展示（富文本）

    # 视频介绍
    video_url: Mapped[str | None] = mapped_column(
        String(255), nullable=True)  # 视频链接
    video_cover: Mapped[str | None] = mapped_column(
        String(255), nullable=True)  # 视频封面

    # SEO设置
    seo_title: Mapped[str | None] = mapped_column(
        String(100), nullable=True)  # SEO标题
    seo_description: Mapped[str | None] = mapped_column(
        String(500), nullable=True)  # SEO描述
    seo_keywords: Mapped[str | None] = mapped_column(
        String(500), nullable=True)  # SEO关键词

    # 主题设置
    theme_color: Mapped[str | None] = mapped_column(
        String(20), nullable=True)  # 主题颜色
    background_color: Mapped[str | None] = mapped_column(
        String(20), nullable=True)  # 背景颜色

    # 其他设置
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否发布
    view_count: Mapped[int] = mapped_column(Integer, default=0)  # 浏览量

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    lawyer: Mapped[Lawyer] = relationship("Lawyer", backref="homepage")


class LawyerPromotionLink(Base):
    """律师推广链接表"""
    __tablename__: str = "lawyer_promotion_links"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lawyers.id"), nullable=False, index=True)
    link_code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True)  # 推广链接码
    link_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True)  # 链接名称
    description: Mapped[str | None] = mapped_column(Text, nullable=True)  # 描述
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True)  # 是否启用
    click_count: Mapped[int] = mapped_column(Integer, default=0)  # 点击次数
    consultation_count: Mapped[int] = mapped_column(Integer, default=0)  # 咨询次数
    conversion_count: Mapped[int] = mapped_column(
        Integer, default=0)  # 转化次数（完成咨询）
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    lawyer: Mapped[Lawyer] = relationship("Lawyer", backref="promotion_links")
