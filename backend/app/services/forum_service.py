"""论坛服务

⚠️ 已迁移到 services/forum/
⚠️ 本文件仅用于向后兼容，请使用新导入路径

迁移时间: 2026-01-22
"""
from .forum import (
    forum_service,
    ForumService,
    get_forum_service,
    forum_post_service,
    ForumPostService,
    forum_comment_service,
    ForumCommentService,
)

__all__ = [
    "forum_service",
    "ForumService",
    "get_forum_service",
    "forum_post_service",
    "ForumPostService",
    "forum_comment_service",
    "ForumCommentService",
]
