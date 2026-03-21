"""新闻服务路由"""
from .news import router as news_router
from .comment import router as comment_router
from .subscription import router as subscription_router

__all__ = ["news_router", "comment_router", "subscription_router"]
