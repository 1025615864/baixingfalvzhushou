"""论坛模型"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .user import User
    from .lawfirm import Lawyer


class Post(Base):
    """帖子表"""

    __tablename__: str = "posts"
    
    # 复合索引优化常用查询
    __table_args__ = (
        Index('ix_posts_pinned_created', 'is_pinned', 'created_at', 'is_deleted'),
        Index('ix_posts_category_created', 'category', 'created_at', 'is_deleted'),
        Index('ix_posts_review_status', 'review_status', 'created_at'),
        Index('ix_posts_heat_score', 'heat_score', 'is_deleted'),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 分类：general/labor/marriage/contract/other
    category: Mapped[str] = mapped_column(String(50), default="general")
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)  # 分享次数
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)  # 置顶
    is_hot: Mapped[bool] = mapped_column(Boolean, default=False)  # 热门标记
    is_essence: Mapped[bool] = mapped_column(Boolean, default=False)  # 精华帖
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    review_status: Mapped[str | None] = mapped_column(
        # pending/approved/rejected
        String(20), default="approved", nullable=True)
    review_reason: Mapped[str | None] = mapped_column(
        String(200), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    heat_score: Mapped[float] = mapped_column(Float, default=0.0)  # 热度分数
    cover_image: Mapped[str | None] = mapped_column(
        String(500), nullable=True)  # 封面图
    images: Mapped[str | None] = mapped_column(Text, nullable=True)  # 图片列表JSON
    attachments: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # 附件列表JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    author: Mapped[User] = relationship("User", backref="posts")
    comments: Mapped[list[Comment]] = relationship(
        "Comment", back_populates="post")
    likes: Mapped[list[PostLike]] = relationship(
        "PostLike", back_populates="post")
    favorites: Mapped[list[PostFavorite]] = relationship(
        "PostFavorite", back_populates="post")


class Comment(Base):
    """评论表"""

    __tablename__: str = "comments"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("comments.id"), nullable=True)  # 回复评论
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    images: Mapped[str | None] = mapped_column(Text, nullable=True)  # 评论图片JSON
    review_status: Mapped[str | None] = mapped_column(
        # pending/approved/rejected
        String(20), default="approved", nullable=True)
    review_reason: Mapped[str | None] = mapped_column(
        String(200), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True)

    # 关系
    post: Mapped[Post] = relationship("Post", back_populates="comments")
    author: Mapped[User] = relationship("User", backref="comments")
    parent: Mapped[Comment | None] = relationship(
        "Comment",
        remote_side="Comment.id",
        foreign_keys="Comment.parent_id",
        back_populates="replies",
        lazy="joined",
    )
    replies: Mapped[list[Comment]] = relationship(
        "Comment",
        foreign_keys="Comment.parent_id",
        back_populates="parent",
        lazy="selectin",
    )


class PostLike(Base):
    """帖子点赞表"""

    __tablename__: str = "post_likes"
    __table_args__: tuple[UniqueConstraint, ...] = (
        UniqueConstraint("post_id", "user_id", name="uq_post_like_post_user"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    # 关系
    post: Mapped[Post] = relationship("Post", back_populates="likes")
    user: Mapped[User] = relationship("User", backref="post_likes")


class CommentLike(Base):
    """评论点赞表"""

    __tablename__: str = "comment_likes"
    __table_args__: tuple[UniqueConstraint, ...] = (
        UniqueConstraint(
            "comment_id",
            "user_id",
            name="uq_comment_like_comment_user"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    comment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("comments.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    # 关系
    comment: Mapped[Comment] = relationship("Comment", backref="likes")
    user: Mapped[User] = relationship("User", backref="comment_likes")


class PostFavorite(Base):
    """帖子收藏表"""

    __tablename__: str = "post_favorites"
    __table_args__: tuple[UniqueConstraint, ...] = (
        UniqueConstraint(
            "post_id",
            "user_id",
            name="uq_post_favorite_post_user"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    # 关系
    post: Mapped[Post] = relationship("Post", back_populates="favorites")
    user: Mapped[User] = relationship("User", backref="post_favorites")


class PostReaction(Base):
    """帖子表情反应表"""

    __tablename__: str = "post_reactions"
    __table_args__: tuple[UniqueConstraint, ...] = (
        UniqueConstraint(
            "post_id",
            "user_id",
            "emoji",
            name="uq_post_reaction"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False)
    emoji: Mapped[str] = mapped_column(String(20), nullable=False)  # 表情符号或代码
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    # 关系
    post: Mapped[Post] = relationship("Post", backref="reactions")
    user: Mapped[User] = relationship("User", backref="post_reactions")


class ForumLawyerInvitation(Base):
    """论坛律师邀请表"""

    __tablename__: str = "forum_lawyer_invitations"
    __table_args__: tuple[UniqueConstraint, ...] = (
        UniqueConstraint(
            "post_id",
            "lawyer_id",
            name="uq_forum_lawyer_invitation_post_lawyer"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id"), nullable=False)
    lawyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lawyers.id"), nullable=False)
    invited_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False)  # 邀请人用户ID
    # pending/accepted/declined/expired
    status: Mapped[str] = mapped_column(String(20), default="pending")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)  # 邀请消息
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)  # 响应时间
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)  # 过期时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    post: Mapped[Post] = relationship("Post", backref="lawyer_invitations")
    lawyer: Mapped[Lawyer] = relationship(
        "Lawyer", backref="forum_invitations")
    inviter: Mapped[User] = relationship(
        "User",
        foreign_keys=[invited_by],
        backref="sent_lawyer_invitations")
