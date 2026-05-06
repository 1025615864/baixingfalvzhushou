"""Comment 模型"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    author_name: Mapped[str] = mapped_column(String(100), nullable=False, default="匿名用户")
    author_avatar: Mapped[str] = mapped_column(String(500), nullable=True)
    is_lawyer: Mapped[bool] = mapped_column(Boolean, default=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    parent_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    reply_to_user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    reply_to_user_name: Mapped[str] = mapped_column(String(100), nullable=True)

    floor_number: Mapped[int] = mapped_column(Integer, nullable=True)

    like_count: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(20), default="published", index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("idx_comment_post_parent", "post_id", "parent_id"),
        Index("idx_comment_floor", "post_id", "floor_number"),
    )
