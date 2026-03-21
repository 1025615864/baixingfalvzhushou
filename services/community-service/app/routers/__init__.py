"""社区服务路由"""
from .post import router as post_router
from .comment import router as comment_router

__all__ = ["post_router", "comment_router"]
