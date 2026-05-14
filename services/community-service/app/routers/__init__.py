"""路由层"""
from . import post, comment
from .hot import router as hot_router
from .admin import router as admin_router
from .report import router as report_router
from .favorite import router as favorite_router
from .topic import router as topic_router
from .agent import router as agent_router

post_router = post.router
comment_router = comment.router

__all__ = ["post_router", "comment_router", "hot_router", "admin_router", "report_router", "favorite_router", "topic_router", "agent_router"]
