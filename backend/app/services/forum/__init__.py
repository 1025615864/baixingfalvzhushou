"""论坛服务模块

向后兼容导出（2026-01-22）
"""
from .core import ForumService, get_forum_service, forum_service
from .posts import ForumPostService, forum_post_service
from .comments import ForumCommentService, forum_comment_service

__all__ = [
    "ForumService",
    "get_forum_service",
    "forum_service",
    "ForumPostService",
    "forum_post_service",
    "ForumCommentService",
    "forum_comment_service",
]
