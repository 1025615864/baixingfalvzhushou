"""新闻数据模型"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, Boolean, JSON, Index, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class NewsCategory(Base):
    __tablename__ = "news_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(String(200), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    news = relationship("News", back_populates="category")


class NewsTag(Base):
    __tablename__ = "news_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    news_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    news = relationship("News", secondary="news_tag_association", back_populates="tags")


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("news_categories.id"), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str] = mapped_column(String(500), nullable=True)
    author: Mapped[str] = mapped_column(String(100), nullable=True)
    cover_image: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)  # draft, review, approved, published, archived, rejected
    view_count: Mapped[int] = mapped_column(default=0)
    like_count: Mapped[int] = mapped_column(default=0)
    share_count: Mapped[int] = mapped_column(default=0)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    category = relationship("NewsCategory", back_populates="news")
    tags = relationship("NewsTag", secondary="news_tag_association", back_populates="news")

    __table_args__ = (
        Index("idx_news_category_status", "category_id", "status"),
        Index("idx_news_published", "published_at"),
        Index("idx_news_status_published", "status", "published_at"),
    )


class NewsTagAssociation(Base):
    __tablename__ = "news_tag_association"

    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("news_tags.id"), primary_key=True)


class NewsComment(Base):
    __tablename__ = "news_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    news_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_news_comment_created", "news_id", "created_at"),
    )


class UserNewsInteraction(Base):
    __tablename__ = "user_news_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    news_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_liked: Mapped[bool] = mapped_column(Boolean, default=False)
    interacted_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("idx_user_news_unique", "user_id", "news_id", unique=True),)


class NewsSubscription(Base):
    __tablename__ = "news_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("news_categories.id"), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class NewsAuditLog(Base):
    __tablename__ = "news_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id"), nullable=False, index=True)
    operator_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    operator_name: Mapped[str] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    from_status: Mapped[str] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_audit_news_created", "news_id", "created_at"),
        Index("idx_audit_operator_action", "operator_id", "action"),
    )


class NewsEditorAssignment(Base):
    __tablename__ = "news_editor_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id"), nullable=False, index=True)
    editor_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    editor_name: Mapped[str] = mapped_column(String(100), nullable=True)
    assigned_by: Mapped[int] = mapped_column(Integer, nullable=False)
    assigned_by_name: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    review_comment: Mapped[str] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_editor_news_status", "news_id", "status"),
        Index("idx_editor_id_status", "editor_id", "status"),
    )


class NewsOperationStats(Base):
    __tablename__ = "news_operation_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stat_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    total_published: Mapped[int] = mapped_column(Integer, default=0)
    total_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    total_rejected: Mapped[int] = mapped_column(Integer, default=0)
    total_views: Mapped[int] = mapped_column(Integer, default=0)
    total_likes: Mapped[int] = mapped_column(Integer, default=0)
    total_comments: Mapped[int] = mapped_column(Integer, default=0)
    avg_review_hours: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_stats_date_unique", "stat_date", unique=True),
    )
