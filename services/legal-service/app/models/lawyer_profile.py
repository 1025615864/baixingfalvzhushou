from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Boolean, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class LawyerHomepage(Base):
    __tablename__ = "lawyer_homepages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("lawyers.id"), nullable=False, unique=True)
    banner_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    profile_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    slogan: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    specialties_display: Mapped[str | None] = mapped_column(String(500), nullable=True)
    achievements: Mapped[str | None] = mapped_column(Text, nullable=True)
    education: Mapped[str | None] = mapped_column(String(500), nullable=True)
    service_areas: Mapped[str | None] = mapped_column(String(500), nullable=True)
    service_hours: Mapped[str | None] = mapped_column(String(200), nullable=True)
    response_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    wechat_qrcode: Mapped[str | None] = mapped_column(String(500), nullable=True)
    weibo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    zhihu_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    case_studies: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_cover: Mapped[str | None] = mapped_column(String(500), nullable=True)
    seo_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    seo_keywords: Mapped[str | None] = mapped_column(String(500), nullable=True)
    theme_color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    background_color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class LawyerPromotionLink(Base):
    __tablename__ = "lawyer_promotion_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("lawyers.id"), nullable=False, index=True)
    link_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    link_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    consultation_count: Mapped[int] = mapped_column(Integer, default=0)
    conversion_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class LawyerReplyTemplate(Base):
    __tablename__ = "lawyer_reply_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("lawyers.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="general")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))